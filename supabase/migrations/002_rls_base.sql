-- ============================================================
-- HIPNUS COSMETICOS — RLS Base v1
-- Migration 002 — Row Level Security para todas as tabelas
-- Funções auxiliares + políticas por perfil
-- ============================================================


-- ─── Funções auxiliares de RLS ───────────────────────────────────────────────

-- Retorna o UUID do usuário logado via Supabase Auth
create or replace function public.current_user_id()
returns uuid
language sql
stable
as $$
  select id from public.users
  where auth_user_id = auth.uid()
  limit 1;
$$;

-- Retorna o UUID do parceiro associado ao usuário logado
create or replace function public.current_partner_id()
returns uuid
language sql
stable
as $$
  select id from public.partners
  where user_id = public.current_user_id()
  limit 1;
$$;

-- Retorna o UUID da loja associada ao usuário logado (via parceiro)
create or replace function public.current_store_id()
returns uuid
language sql
stable
as $$
  select id from public.stores
  where partner_id = public.current_partner_id()
  limit 1;
$$;

-- Verifica se o usuário logado tem papel admin ou super_admin
create or replace function public.is_admin()
returns boolean
language sql
stable
as $$
  select exists (
    select 1 from public.users
    where auth_user_id = auth.uid()
      and role in ('admin','super_admin')
  );
$$;

-- Verifica se o usuário logado é parceiro ativo
create or replace function public.is_partner()
returns boolean
language sql
stable
as $$
  select exists (
    select 1 from public.partners p
    join public.users u on u.id = p.user_id
    where u.auth_user_id = auth.uid()
      and p.status = 'active'
  );
$$;

comment on function public.current_user_id  is 'UUID do usuário logado em public.users.';
comment on function public.current_partner_id is 'UUID do parceiro do usuário logado.';
comment on function public.current_store_id  is 'UUID da loja do usuário logado.';
comment on function public.is_admin          is 'True se o usuário logado é admin ou super_admin.';
comment on function public.is_partner        is 'True se o usuário logado é parceiro ativo.';


-- ─── RLS: USERS ──────────────────────────────────────────────────────────────
alter table public.users enable row level security;

create policy users_select_own on public.users
  for select using (
    public.is_admin()
    or auth_user_id = auth.uid()
  );

create policy users_update_own on public.users
  for update using (auth_user_id = auth.uid())
  with check (auth_user_id = auth.uid());

create policy users_insert_service on public.users
  for insert with check (true);  -- trigger de auth.users controla inserção


-- ─── RLS: PARTNERS ───────────────────────────────────────────────────────────
alter table public.partners enable row level security;

create policy partners_select on public.partners
  for select using (
    public.is_admin()
    or user_id = public.current_user_id()
  );

create policy partners_insert_own on public.partners
  for insert with check (
    user_id = public.current_user_id()
  );

create policy partners_update_admin on public.partners
  for update using (public.is_admin())
  with check (public.is_admin());


-- ─── RLS: STORES ─────────────────────────────────────────────────────────────
alter table public.stores enable row level security;

create policy stores_select_all on public.stores
  for select using (is_active = true or public.is_admin());

create policy stores_write_own on public.stores
  for all using (
    public.is_admin()
    or partner_id = public.current_partner_id()
  ) with check (
    public.is_admin()
    or partner_id = public.current_partner_id()
  );


-- ─── RLS: PRODUCT_LINES ──────────────────────────────────────────────────────
alter table public.product_lines enable row level security;

create policy product_lines_select_all on public.product_lines
  for select using (true);

create policy product_lines_write_admin on public.product_lines
  for all using (public.is_admin())
  with check (public.is_admin());


-- ─── RLS: PRODUCTS ───────────────────────────────────────────────────────────
alter table public.products enable row level security;

create policy products_select_all on public.products
  for select using (true);

create policy products_write_admin on public.products
  for all using (public.is_admin())
  with check (public.is_admin());


-- ─── RLS: PRODUCT_PRICES ─────────────────────────────────────────────────────
alter table public.product_prices enable row level security;

create policy product_prices_select_all on public.product_prices
  for select using (true);

create policy product_prices_write_admin on public.product_prices
  for all using (public.is_admin())
  with check (public.is_admin());


-- ─── RLS: STORE_PRODUCTS ─────────────────────────────────────────────────────
alter table public.store_products enable row level security;

create policy store_products_select_active on public.store_products
  for select using (
    is_visible = true
    or public.is_admin()
    or store_id = public.current_store_id()
  );

create policy store_products_write_own on public.store_products
  for all using (
    public.is_admin()
    or store_id = public.current_store_id()
  ) with check (
    public.is_admin()
    or store_id = public.current_store_id()
  );


-- ─── RLS: STORE_CUSTOMERS ────────────────────────────────────────────────────
alter table public.store_customers enable row level security;

create policy store_customers_select on public.store_customers
  for select using (
    public.is_admin()
    or user_id = public.current_user_id()
    or store_id = public.current_store_id()
  );

create policy store_customers_insert_own on public.store_customers
  for insert with check (user_id = public.current_user_id());


-- ─── RLS: PLATFORM_SETTINGS ──────────────────────────────────────────────────
-- (habilitado também na migration 003_rls_additions.sql — idempotente)
alter table public.platform_settings enable row level security;

create policy platform_settings_select_all on public.platform_settings
  for select using (true);

create policy platform_settings_write_admin on public.platform_settings
  for all using (public.is_admin())
  with check (public.is_admin());


-- ─── RLS: ADDRESSES ──────────────────────────────────────────────────────────
-- (habilitado também na migration 003_rls_additions.sql — idempotente)
alter table public.addresses enable row level security;

create policy addresses_select_own on public.addresses
  for select using (
    public.is_admin()
    or user_id = public.current_user_id()
  );

create policy addresses_write_own on public.addresses
  for all using (
    public.is_admin()
    or user_id = public.current_user_id()
  ) with check (
    user_id = public.current_user_id()
  );


-- ─── RLS: INVENTORY ──────────────────────────────────────────────────────────
alter table public.inventory_locations enable row level security;
alter table public.inventory_balances  enable row level security;
alter table public.inventory_movements enable row level security;

create policy inventory_locations_select on public.inventory_locations
  for select using (
    public.is_admin()
    or (type = 'store' and store_id = public.current_store_id())
  );

create policy inventory_locations_write_admin on public.inventory_locations
  for all using (public.is_admin())
  with check (public.is_admin());

create policy inventory_balances_select on public.inventory_balances
  for select using (
    public.is_admin()
    or location_id in (
      select id from public.inventory_locations
      where store_id = public.current_store_id()
    )
  );

create policy inventory_movements_select on public.inventory_movements
  for select using (
    public.is_admin()
    or location_id in (
      select id from public.inventory_locations
      where store_id = public.current_store_id()
    )
  );


-- ─── RLS: SUPPLY_ORDERS ──────────────────────────────────────────────────────
alter table public.supply_orders       enable row level security;
alter table public.supply_order_items  enable row level security;

create policy supply_orders_select on public.supply_orders
  for select using (
    public.is_admin()
    or partner_id = public.current_partner_id()
  );

create policy supply_orders_insert_partner on public.supply_orders
  for insert with check (
    partner_id = public.current_partner_id()
  );

create policy supply_orders_update on public.supply_orders
  for update using (
    public.is_admin()
    or (partner_id = public.current_partner_id() and status = 'draft')
  );

create policy supply_order_items_select on public.supply_order_items
  for select using (
    public.is_admin()
    or supply_order_id in (
      select id from public.supply_orders
      where partner_id = public.current_partner_id()
    )
  );

create policy supply_order_items_write on public.supply_order_items
  for all using (
    public.is_admin()
    or supply_order_id in (
      select id from public.supply_orders
      where partner_id = public.current_partner_id() and status = 'draft'
    )
  );


-- ─── RLS: SALES_ORDERS ───────────────────────────────────────────────────────
alter table public.sales_orders       enable row level security;
alter table public.sales_order_items  enable row level security;

create policy sales_orders_select on public.sales_orders
  for select using (
    public.is_admin()
    or customer_id = public.current_user_id()
    or store_id = public.current_store_id()
  );

create policy sales_orders_insert_customer on public.sales_orders
  for insert with check (
    customer_id = public.current_user_id()
  );

create policy sales_order_items_select on public.sales_order_items
  for select using (
    public.is_admin()
    or sales_order_id in (
      select id from public.sales_orders
      where customer_id = public.current_user_id()
         or store_id = public.current_store_id()
    )
  );


-- ─── RLS: PAYMENTS ───────────────────────────────────────────────────────────
alter table public.payments enable row level security;

create policy payments_select on public.payments
  for select using (
    public.is_admin()
    or (
      order_type = 'sales_order' and order_id in (
        select id from public.sales_orders
        where customer_id = public.current_user_id()
           or store_id = public.current_store_id()
      )
    )
    or (
      order_type = 'supply_order' and order_id in (
        select id from public.supply_orders
        where partner_id = public.current_partner_id()
      )
    )
  );

create policy payments_write_service on public.payments
  for all using (public.is_admin())
  with check (public.is_admin());


-- ─── RLS: SHIPMENTS ──────────────────────────────────────────────────────────
alter table public.shipments enable row level security;

create policy shipments_select on public.shipments
  for select using (
    public.is_admin()
    or (
      order_type = 'sales_order' and order_id in (
        select id from public.sales_orders
        where customer_id = public.current_user_id()
           or store_id = public.current_store_id()
      )
    )
    or (
      order_type = 'supply_order' and order_id in (
        select id from public.supply_orders
        where partner_id = public.current_partner_id()
      )
    )
  );

create policy shipments_write_admin on public.shipments
  for all using (public.is_admin())
  with check (public.is_admin());


-- ─── RLS: COMMISSIONS ────────────────────────────────────────────────────────
alter table public.commissions enable row level security;

create policy commissions_select on public.commissions
  for select using (
    public.is_admin()
    or sales_order_id in (
      select id from public.sales_orders
      where store_id = public.current_store_id()
    )
  );


-- ─── Trigger: sincronizar auth.users → public.users ─────────────────────────
create or replace function public.fn_sync_auth_user()
returns trigger
language plpgsql
security definer
as $$
begin
  insert into public.users (auth_user_id, name, email, role)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'name', split_part(new.email, '@', 1)),
    new.email,
    coalesce(new.raw_user_meta_data->>'role', 'cliente')
  )
  on conflict (auth_user_id) do update
    set email      = excluded.email,
        updated_at = now();
  return new;
end;
$$;

create trigger trg_sync_auth_user
  after insert or update on auth.users
  for each row execute function public.fn_sync_auth_user();

comment on function public.fn_sync_auth_user is
  'Sincroniza automaticamente auth.users → public.users ao criar/atualizar conta Supabase Auth.';
