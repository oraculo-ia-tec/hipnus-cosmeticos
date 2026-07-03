
-- ============================================================
-- HIPNUS COSMETICOS - Triggers e Functions v2
-- Ajuste: taxa de plataforma via platform_settings (nao hardcoded)
-- ============================================================

create or replace function public.fn_supply_order_status_change()
returns trigger
language plpgsql
security definer
as $$
declare
  v_central_location_id uuid;
  v_store_location_id uuid;
  v_store_id uuid;
  v_item record;
begin
  if new.status = 'delivered' and old.status != 'delivered' then

    select id into v_central_location_id
    from public.inventory_locations
    where type = 'central';

    select s.id into v_store_id
    from public.stores s
    where s.partner_id = new.partner_id;

    select id into v_store_location_id
    from public.inventory_locations
    where type = 'store' and store_id = v_store_id;

    for v_item in
      select product_id, quantity from public.supply_order_items
      where supply_order_id = new.id
    loop
      update public.inventory_balances
        set quantity = quantity - v_item.quantity, updated_at = now()
        where location_id = v_central_location_id and product_id = v_item.product_id;

      insert into public.inventory_movements
        (location_id, product_id, movement_type, quantity, reference_type, reference_id, created_by)
      values
        (v_central_location_id, v_item.product_id, 'transferencia', -v_item.quantity, 'supply_order', new.id, null);

      insert into public.inventory_balances (location_id, product_id, quantity, updated_at)
      values (v_store_location_id, v_item.product_id, v_item.quantity, now())
      on conflict (location_id, product_id)
      do update set quantity = public.inventory_balances.quantity + v_item.quantity, updated_at = now();

      insert into public.inventory_movements
        (location_id, product_id, movement_type, quantity, reference_type, reference_id, created_by)
      values
        (v_store_location_id, v_item.product_id, 'entrada_compra', v_item.quantity, 'supply_order', new.id, null);

    end loop;
  end if;

  return new;
end;
$$;

create trigger trg_supply_order_status_change
  after update of status on public.supply_orders
  for each row
  execute function public.fn_supply_order_status_change();

comment on function public.fn_supply_order_status_change is
  'Ao entregar pedido de abastecimento: baixa estoque central e credita estoque da loja do parceiro, gerando movimentos de auditoria.';


create or replace function public.fn_sales_order_status_change()
returns trigger
language plpgsql
security definer
as $$
declare
  v_store_location_id uuid;
  v_item record;
begin
  if new.status = 'paid' and old.status != 'paid' then

    select id into v_store_location_id
    from public.inventory_locations
    where type = 'store' and store_id = new.store_id;

    for v_item in
      select product_id, quantity from public.sales_order_items
      where sales_order_id = new.id
    loop
      update public.inventory_balances
        set quantity = quantity - v_item.quantity, updated_at = now()
        where location_id = v_store_location_id and product_id = v_item.product_id;

      insert into public.inventory_movements
        (location_id, product_id, movement_type, quantity, reference_type, reference_id, created_by)
      values
        (v_store_location_id, v_item.product_id, 'saida_venda', -v_item.quantity, 'sales_order', new.id, new.customer_id);
    end loop;

  end if;

  if new.status in ('canceled','refunded') and old.status = 'paid' then

    select id into v_store_location_id
    from public.inventory_locations
    where type = 'store' and store_id = new.store_id;

    for v_item in
      select product_id, quantity from public.sales_order_items
      where sales_order_id = new.id
    loop
      update public.inventory_balances
        set quantity = quantity + v_item.quantity, updated_at = now()
        where location_id = v_store_location_id and product_id = v_item.product_id;

      insert into public.inventory_movements
        (location_id, product_id, movement_type, quantity, reference_type, reference_id, created_by)
      values
        (v_store_location_id, v_item.product_id, 'devolucao', v_item.quantity, 'sales_order', new.id, new.customer_id);
    end loop;

  end if;

  return new;
end;
$$;

create trigger trg_sales_order_status_change
  after update of status on public.sales_orders
  for each row
  execute function public.fn_sales_order_status_change();

comment on function public.fn_sales_order_status_change is
  'Ao confirmar pagamento: baixa estoque da loja. Ao cancelar/reembolsar pedido pago: devolve estoque.';


create or replace function public.fn_recalc_sales_order_totals()
returns trigger
language plpgsql
security definer
as $$
declare
  v_order_id uuid;
begin
  v_order_id := coalesce(new.sales_order_id, old.sales_order_id);

  update public.sales_orders so
  set
    total_amount = coalesce((
      select sum(unit_sale_price * quantity) from public.sales_order_items
      where sales_order_id = v_order_id
    ), 0),
    floor_total = coalesce((
      select sum(unit_floor_price * quantity) from public.sales_order_items
      where sales_order_id = v_order_id
    ), 0),
    partner_margin_total = coalesce((
      select sum((unit_sale_price - unit_floor_price) * quantity) from public.sales_order_items
      where sales_order_id = v_order_id
    ), 0),
    updated_at = now()
  where so.id = v_order_id;

  return coalesce(new, old);
end;
$$;

create trigger trg_recalc_sales_order_totals
  after insert or update or delete on public.sales_order_items
  for each row
  execute function public.fn_recalc_sales_order_totals();

comment on function public.fn_recalc_sales_order_totals is
  'Mantem total_amount, floor_total e partner_margin_total do sales_order sempre sincronizados com os itens.';


-- Ajuste principal: taxa de plataforma agora lida de platform_settings
create or replace function public.fn_generate_commission()
returns trigger
language plpgsql
security definer
as $$
declare
  v_order record;
  v_platform_fee_rate numeric;
  v_platform_fee numeric;
  v_partner_amount numeric;
  v_hipnus_amount numeric;
begin
  if new.order_type = 'sales_order' and new.status = 'confirmed' and old.status != 'confirmed' then

    select value into v_platform_fee_rate
    from public.platform_settings where key = 'platform_fee_rate';

    v_platform_fee_rate := coalesce(v_platform_fee_rate, 0.03);

    select * into v_order from public.sales_orders where id = new.order_id;

    v_platform_fee := v_order.partner_margin_total * v_platform_fee_rate;
    v_partner_amount := v_order.partner_margin_total - v_platform_fee;
    v_hipnus_amount := v_order.floor_total + v_platform_fee;

    insert into public.commissions
      (sales_order_id, hipnus_amount, partner_amount, platform_fee)
    values
      (v_order.id, v_hipnus_amount, v_partner_amount, v_platform_fee)
    on conflict (sales_order_id) do update
      set hipnus_amount = excluded.hipnus_amount,
          partner_amount = excluded.partner_amount,
          platform_fee = excluded.platform_fee;

    update public.sales_orders set status = 'paid' where id = v_order.id;

  end if;

  return new;
end;
$$;

create trigger trg_generate_commission
  after update of status on public.payments
  for each row
  execute function public.fn_generate_commission();

comment on function public.fn_generate_commission is
  'Ao confirmar pagamento Asaas de uma venda: le taxa em platform_settings, calcula split e marca pedido como pago.';


create or replace function public.fn_set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger trg_users_updated_at before update on public.users
  for each row execute function public.fn_set_updated_at();
create trigger trg_partners_updated_at before update on public.partners
  for each row execute function public.fn_set_updated_at();
create trigger trg_stores_updated_at before update on public.stores
  for each row execute function public.fn_set_updated_at();
create trigger trg_products_updated_at before update on public.products
  for each row execute function public.fn_set_updated_at();
create trigger trg_store_products_updated_at before update on public.store_products
  for each row execute function public.fn_set_updated_at();
create trigger trg_supply_orders_updated_at before update on public.supply_orders
  for each row execute function public.fn_set_updated_at();
create trigger trg_sales_orders_updated_at before update on public.sales_orders
  for each row execute function public.fn_set_updated_at();
