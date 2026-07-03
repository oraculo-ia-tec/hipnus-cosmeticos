
-- ============================================================
-- HIPNUS COSMETICOS - Views para consumo direto no Streamlit
-- Pensadas para dashboard admin, catalogo por role e operacao.
-- ============================================================

-- 1. Dashboard admin - KPIs gerais
create or replace view public.v_admin_dashboard_kpis as
select
  (select count(*) from public.users where role = 'cliente' and is_active = true) as total_clientes_ativos,
  (select count(*) from public.partners where status = 'active') as total_parceiros_ativos,
  (select count(*) from public.stores where is_active = true) as total_lojas_ativas,
  (select count(*) from public.sales_orders) as total_pedidos_venda,
  (select count(*) from public.supply_orders) as total_pedidos_abastecimento,
  (select coalesce(sum(total_amount),0) from public.sales_orders where status in ('paid','shipped','delivered')) as faturamento_vendas,
  (select coalesce(sum(total_amount),0) from public.supply_orders where status in ('approved','picking','invoiced','shipped','delivered')) as faturamento_abastecimento,
  (select coalesce(sum(platform_fee),0) from public.commissions) as receita_plataforma,
  (select count(*) from public.payments where status = 'pending') as pagamentos_pendentes,
  (select count(*) from public.shipments where status in ('pending','picking','shipped','in_transit')) as entregas_em_aberto;

comment on view public.v_admin_dashboard_kpis is 'KPIs consolidados para painel admin/super_admin.';

-- 2. Dashboard admin - pedidos de venda detalhados
create or replace view public.v_admin_sales_orders as
select
  so.id,
  so.created_at,
  so.status,
  so.channel,
  so.total_amount,
  so.floor_total,
  so.partner_margin_total,
  st.id as store_id,
  st.display_name as store_name,
  p.id as partner_id,
  p.name as partner_name,
  u.id as customer_id,
  u.name as customer_name,
  u.email as customer_email,
  pay.status as payment_status,
  pay.method as payment_method,
  sh.status as shipment_status,
  sh.tracking_code
from public.sales_orders so
join public.stores st on st.id = so.store_id
join public.partners p on p.id = st.partner_id
join public.users u on u.id = so.customer_id
left join public.payments pay on pay.order_type = 'sales_order' and pay.order_id = so.id
left join public.shipments sh on sh.order_type = 'sales_order' and sh.order_id = so.id;

comment on view public.v_admin_sales_orders is 'Pedidos da loja para o cliente final, com cliente, parceiro, pagamento e entrega.';

-- 3. Dashboard admin - pedidos de abastecimento
create or replace view public.v_admin_supply_orders as
select
  so.id,
  so.created_at,
  so.status,
  so.total_amount,
  p.id as partner_id,
  p.name as partner_name,
  p.partner_type,
  st.id as store_id,
  st.display_name as store_name,
  pay.status as payment_status,
  pay.method as payment_method,
  sh.status as shipment_status,
  sh.tracking_code
from public.supply_orders so
join public.partners p on p.id = so.partner_id
left join public.stores st on st.partner_id = p.id
left join public.payments pay on pay.order_type = 'supply_order' and pay.order_id = so.id
left join public.shipments sh on sh.order_type = 'supply_order' and sh.order_id = so.id;

comment on view public.v_admin_supply_orders is 'Pedidos de abastecimento B2B feitos por distribuidor/salao para a Hipnus.';

-- 4. Dashboard admin - estoque central
create or replace view public.v_admin_central_inventory as
select
  il.id as location_id,
  il.name as location_name,
  pr.id as product_id,
  pr.sku,
  pr.name as product_name,
  pl.name as line_name,
  ib.quantity,
  ib.updated_at
from public.inventory_balances ib
join public.inventory_locations il on il.id = ib.location_id
join public.products pr on pr.id = ib.product_id
left join public.product_lines pl on pl.id = pr.line_id
where il.type = 'central';

comment on view public.v_admin_central_inventory is 'Estoque central da Hipnus para operacao do admin.';

-- 5. Dashboard admin - estoque das lojas
create or replace view public.v_admin_store_inventory as
select
  st.id as store_id,
  st.display_name as store_name,
  p.name as partner_name,
  p.partner_type,
  pr.id as product_id,
  pr.sku,
  pr.name as product_name,
  ib.quantity,
  ib.updated_at
from public.inventory_balances ib
join public.inventory_locations il on il.id = ib.location_id and il.type = 'store'
join public.stores st on st.id = il.store_id
join public.partners p on p.id = st.partner_id
join public.products pr on pr.id = ib.product_id;

comment on view public.v_admin_store_inventory is 'Estoque por loja/parceiro para acompanhamento administrativo.';

-- 6. Catalogo do parceiro para abastecimento B2B
create or replace view public.v_partner_supply_catalog as
select
  pr.id as product_id,
  pr.sku,
  pr.name as product_name,
  pr.description,
  pr.image_url,
  pl.name as line_name,
  floor_price.price as floor_price,
  distrib_price.price as distribuidor_price,
  salao_price.price as salao_price
from public.products pr
left join public.product_lines pl on pl.id = pr.line_id
left join public.product_prices floor_price
  on floor_price.product_id = pr.id and floor_price.price_type = 'floor' and floor_price.valid_to is null
left join public.product_prices distrib_price
  on distrib_price.product_id = pr.id and distrib_price.price_type = 'distribuidor' and distrib_price.valid_to is null
left join public.product_prices salao_price
  on salao_price.product_id = pr.id and salao_price.price_type = 'salao' and salao_price.valid_to is null
where pr.is_active = true;

comment on view public.v_partner_supply_catalog is 'Catalogo B2B da Hipnus para compra de abastecimento por parceiros.';

-- 7. Catalogo visivel da loja para o cliente final
create or replace view public.v_store_customer_catalog as
select
  sp.store_id,
  st.display_name as store_name,
  pr.id as product_id,
  pr.sku,
  pr.name as product_name,
  pr.description,
  pr.image_url,
  pl.name as line_name,
  sp.sale_price,
  coalesce(ib.quantity, 0) as stock_quantity,
  sp.is_visible
from public.store_products sp
join public.stores st on st.id = sp.store_id
join public.products pr on pr.id = sp.product_id
left join public.product_lines pl on pl.id = pr.line_id
left join public.inventory_locations il on il.store_id = sp.store_id and il.type = 'store'
left join public.inventory_balances ib on ib.location_id = il.id and ib.product_id = sp.product_id
where sp.is_visible = true and pr.is_active = true;

comment on view public.v_store_customer_catalog is 'Catalogo B2C por loja personalizada, com estoque e preco final.';

-- 8. Minha Conta - pedidos do cliente
create or replace view public.v_my_orders as
select
  so.id,
  so.created_at,
  so.status,
  so.total_amount,
  so.channel,
  st.id as store_id,
  st.display_name as store_name,
  pay.status as payment_status,
  pay.method as payment_method,
  sh.status as shipment_status,
  sh.tracking_code
from public.sales_orders so
join public.stores st on st.id = so.store_id
left join public.payments pay on pay.order_type = 'sales_order' and pay.order_id = so.id
left join public.shipments sh on sh.order_type = 'sales_order' and sh.order_id = so.id;

comment on view public.v_my_orders is 'Base da aba Meus Pedidos do cliente.';

-- 9. Minha Conta - pagamentos do cliente
create or replace view public.v_my_payments as
select
  pay.id,
  pay.created_at,
  pay.amount,
  pay.status,
  pay.method,
  pay.order_id as sales_order_id,
  so.status as order_status,
  st.display_name as store_name,
  pay.asaas_payment_id,
  pay.paid_at
from public.payments pay
join public.sales_orders so on pay.order_type = 'sales_order' and so.id = pay.order_id
join public.stores st on st.id = so.store_id;

comment on view public.v_my_payments is 'Base da aba Meus Pagamentos do cliente.';

-- 10. Parceiro - pedidos da propria loja
create or replace view public.v_partner_store_orders as
select
  so.id,
  so.created_at,
  so.status,
  so.total_amount,
  so.channel,
  u.name as customer_name,
  u.email as customer_email,
  pay.status as payment_status,
  pay.method as payment_method,
  sh.status as shipment_status,
  sh.tracking_code,
  so.store_id
from public.sales_orders so
join public.users u on u.id = so.customer_id
left join public.payments pay on pay.order_type = 'sales_order' and pay.order_id = so.id
left join public.shipments sh on sh.order_type = 'sales_order' and sh.order_id = so.id;

comment on view public.v_partner_store_orders is 'Pedidos recebidos pela loja do parceiro.';

-- 11. Parceiro - estoque da propria loja
create or replace view public.v_partner_store_inventory as
select
  st.id as store_id,
  pr.id as product_id,
  pr.sku,
  pr.name as product_name,
  pl.name as line_name,
  coalesce(ib.quantity,0) as quantity,
  sp.sale_price,
  sp.is_visible,
  ib.updated_at
from public.store_products sp
join public.stores st on st.id = sp.store_id
join public.products pr on pr.id = sp.product_id
left join public.product_lines pl on pl.id = pr.line_id
left join public.inventory_locations il on il.store_id = st.id and il.type = 'store'
left join public.inventory_balances ib on ib.location_id = il.id and ib.product_id = pr.id;

comment on view public.v_partner_store_inventory is 'Estoque e preco dos produtos da loja do parceiro.';
