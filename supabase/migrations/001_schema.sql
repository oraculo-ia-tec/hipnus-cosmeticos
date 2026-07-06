-- ============================================================
-- HIPNUS COSMETICOS — Schema Base v1
-- Migration 001 — Todas as tabelas principais
-- Reconstruída a partir dos models SQLAlchemy e referências
-- nas migrations 003-007 e views 005.
-- ============================================================

-- ─── Extensões ────────────────────────────────────────────────────────────────
create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

-- ─── Função utilitária: atualiza updated_at automaticamente ──────────────────
create or replace function public.fn_set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

comment on function public.fn_set_updated_at is
  'Trigger genérico para atualizar updated_at em qualquer tabela.';


-- ─── 1. USERS ─────────────────────────────────────────────────────────────────
-- Espelha auth.users do Supabase Auth com dados de perfil da plataforma.
create table public.users (
    id              uuid primary key default gen_random_uuid(),
    auth_user_id    uuid unique references auth.users(id) on delete cascade,
    name            varchar(120) not null,
    username        varchar(60)  unique,
    email           varchar(180) not null unique,
    display_name    varchar(120),
    role            varchar(30)  not null default 'cliente'
                       check (role in ('super_admin','admin','b2b','b2c','cliente','demo')),
    is_active       boolean      not null default true,
    is_verified     boolean      not null default false,
    phone           varchar(32),
    created_at      timestamptz  not null default now(),
    updated_at      timestamptz  not null default now()
);
comment on table public.users is 'Perfis de todos os usuários da plataforma (admin, parceiro, cliente).';

create trigger trg_users_updated_at
  before update on public.users
  for each row execute function public.fn_set_updated_at();

create index idx_users_email    on public.users(email);
create index idx_users_role     on public.users(role);


-- ─── 2. PARTNERS ─────────────────────────────────────────────────────────────
-- Parceiros B2B (distribuidores, salões, revendedores).
create table public.partners (
    id               uuid primary key default gen_random_uuid(),
    user_id          uuid references public.users(id) on delete set null,
    name             varchar(255) not null,
    legal_name       varchar(255),
    email            varchar(255) not null unique,
    phone            varchar(32),
    cpf_cnpj         varchar(20)  not null unique,
    partner_type     varchar(30)  not null default 'revendedor'
                        check (partner_type in ('profissional','salao','distribuidor','revendedor')),
    status           varchar(20)  not null default 'pending'
                        check (status in ('pending','active','suspended','rejected')),
    -- Dados Asaas (subconta / wallet)
    asaas_account_id varchar(64)  unique,
    asaas_wallet_id  varchar(64),
    asaas_api_key    varchar(255),
    is_active        boolean      not null default true,
    created_at       timestamptz  not null default now(),
    updated_at       timestamptz  not null default now()
);
comment on table public.partners is 'Parceiros da plataforma (distribuidores, salões, revendedores).';

create trigger trg_partners_updated_at
  before update on public.partners
  for each row execute function public.fn_set_updated_at();

create index idx_partners_status   on public.partners(status);
create index idx_partners_cpf_cnpj on public.partners(cpf_cnpj);


-- ─── 3. STORES ────────────────────────────────────────────────────────────────
-- Loja online 1:1 com cada parceiro.
create table public.stores (
    id           uuid primary key default gen_random_uuid(),
    partner_id   uuid not null unique references public.partners(id) on delete cascade,
    slug         varchar(120) not null unique,
    display_name varchar(160) not null,
    description  text,
    logo_url     varchar(512),
    primary_color varchar(9) default '#7c3aed',
    is_active    boolean not null default true,
    created_at   timestamptz not null default now(),
    updated_at   timestamptz not null default now()
);
comment on table public.stores is 'Vitrine online de cada parceiro (slug único, branding).';

create trigger trg_stores_updated_at
  before update on public.stores
  for each row execute function public.fn_set_updated_at();

create index idx_stores_slug on public.stores(slug);


-- ─── 4. PRODUCT_LINES ────────────────────────────────────────────────────────
-- Linhas/coleções da marca (Turmalina, Ouro, Teia de Aranha, etc.)
create table public.product_lines (
    id          uuid primary key default gen_random_uuid(),
    name        varchar(120) not null unique,
    description text,
    image_url   varchar(512),
    is_active   boolean not null default true,
    display_order integer not null default 0,
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);
comment on table public.product_lines is 'Linhas/coleções do portfólio Hipnus.';

create trigger trg_product_lines_updated_at
  before update on public.product_lines
  for each row execute function public.fn_set_updated_at();


-- ─── 5. PRODUCTS ──────────────────────────────────────────────────────────────
-- Catálogo oficial de produtos Hipnus.
create table public.products (
    id                      uuid primary key default gen_random_uuid(),
    sku                     varchar(64)  not null unique,
    name                    varchar(255) not null,
    description             text,
    category                varchar(40)  not null default 'geral',
    line_id                 uuid references public.product_lines(id) on delete set null,
    is_kit                  boolean not null default false,
    image_url               varchar(512),
    floor_price             numeric(10,2) not null,
    suggested_retail_price  numeric(10,2),
    is_active               boolean not null default true,
    created_at              timestamptz not null default now(),
    updated_at              timestamptz not null default now()
);
comment on table public.products is 'Catálogo oficial de produtos Hipnus (fonte única de verdade).';

create trigger trg_products_updated_at
  before update on public.products
  for each row execute function public.fn_set_updated_at();

create index idx_products_sku     on public.products(sku);
create index idx_products_line    on public.products(line_id);
create index idx_products_active  on public.products(is_active);


-- ─── 6. PRODUCT_PRICES ───────────────────────────────────────────────────────
-- Tabela de preços por tipo (floor, distribuidor, salao).
create table public.product_prices (
    id           uuid primary key default gen_random_uuid(),
    product_id   uuid not null references public.products(id) on delete cascade,
    price_type   varchar(20) not null
                    check (price_type in ('floor','distribuidor','salao','varejo')),
    price        numeric(10,2) not null,
    valid_from   date not null default current_date,
    valid_to     date,
    created_at   timestamptz not null default now()
);
comment on table public.product_prices is 'Tabela de preços por tipo e vigência para o catálogo Hipnus.';

create index idx_product_prices_product on public.product_prices(product_id);
create index idx_product_prices_type    on public.product_prices(price_type, valid_to);


-- ─── 7. STORE_PRODUCTS ───────────────────────────────────────────────────────
-- Produtos disponibilizados pelo parceiro na sua loja (com preço de venda).
create table public.store_products (
    id          uuid primary key default gen_random_uuid(),
    store_id    uuid not null references public.stores(id) on delete cascade,
    product_id  uuid not null references public.products(id) on delete cascade,
    sale_price  numeric(10,2) not null,
    is_visible  boolean not null default true,
    is_featured boolean not null default false,
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now(),
    unique (store_id, product_id)
);
comment on table public.store_products is 'Produtos expostos em cada loja com preço de venda do parceiro.';

create trigger trg_store_products_updated_at
  before update on public.store_products
  for each row execute function public.fn_set_updated_at();

create index idx_store_products_store   on public.store_products(store_id);
create index idx_store_products_product on public.store_products(product_id);


-- ─── 8. STORE_CUSTOMERS ──────────────────────────────────────────────────────
-- Vínculo entre cliente e loja (de qual loja o cliente compra).
create table public.store_customers (
    id          uuid primary key default gen_random_uuid(),
    store_id    uuid not null references public.stores(id) on delete cascade,
    user_id     uuid not null references public.users(id) on delete cascade,
    linked_at   timestamptz not null default now(),
    unique (store_id, user_id)
);
comment on table public.store_customers is 'Vínculo cliente-loja (qual loja o cliente acessa).';

create index idx_store_customers_user  on public.store_customers(user_id);
create index idx_store_customers_store on public.store_customers(store_id);


-- ─── 9. PLATFORM_SETTINGS ────────────────────────────────────────────────────
-- Configurações globais da plataforma (taxa, limites, etc.)
create table public.platform_settings (
    id                  serial primary key,
    platform_fee_rate   numeric(5,4) not null default 0.10,  -- 10% default
    min_order_amount    numeric(10,2) not null default 0.00,
    asaas_split_enabled boolean not null default true,
    updated_at          timestamptz not null default now(),
    updated_by          uuid references public.users(id)
);
comment on table public.platform_settings is 'Configurações globais da plataforma (taxa de plataforma, limites, etc.).';

-- Garante apenas 1 linha de configuração
create unique index idx_platform_settings_singleton on public.platform_settings ((true));

-- Insere configuração padrão
insert into public.platform_settings (platform_fee_rate) values (0.10);


-- ─── 10. ADDRESSES ───────────────────────────────────────────────────────────
-- Endereços dos usuários (entrega, cobrança).
create table public.addresses (
    id           uuid primary key default gen_random_uuid(),
    user_id      uuid not null references public.users(id) on delete cascade,
    label        varchar(40) default 'Casa',
    street       varchar(255) not null,
    number       varchar(20),
    complement   varchar(80),
    neighborhood varchar(100),
    city         varchar(100) not null,
    state        char(2) not null,
    postal_code  varchar(9) not null,
    country      char(2) not null default 'BR',
    is_default   boolean not null default false,
    created_at   timestamptz not null default now(),
    updated_at   timestamptz not null default now()
);
comment on table public.addresses is 'Endereços de entrega e cobrança dos usuários.';

create trigger trg_addresses_updated_at
  before update on public.addresses
  for each row execute function public.fn_set_updated_at();

create index idx_addresses_user on public.addresses(user_id);


-- ─── 11. INVENTORY_LOCATIONS ─────────────────────────────────────────────────
-- Locais de estoque: central (Hipnus) e lojas dos parceiros.
create table public.inventory_locations (
    id       uuid primary key default gen_random_uuid(),
    type     varchar(20) not null check (type in ('central','store')),
    store_id uuid references public.stores(id) on delete cascade,
    name     varchar(120) not null,
    constraint chk_location_store check (
        (type = 'store' and store_id is not null) or
        (type = 'central' and store_id is null)
    )
);
comment on table public.inventory_locations is 'Locais de estoque: armazém central da Hipnus e estoques das lojas.';

create index idx_inventory_locations_type  on public.inventory_locations(type);
create index idx_inventory_locations_store on public.inventory_locations(store_id);


-- ─── 12. INVENTORY_BALANCES ──────────────────────────────────────────────────
-- Saldo atual de cada produto em cada local de estoque.
create table public.inventory_balances (
    id          uuid primary key default gen_random_uuid(),
    location_id uuid not null references public.inventory_locations(id) on delete cascade,
    product_id  uuid not null references public.products(id) on delete cascade,
    quantity    integer not null default 0,
    updated_at  timestamptz not null default now(),
    unique (location_id, product_id)
);
comment on table public.inventory_balances is 'Saldo atual de estoque por produto e local.';

create index idx_inventory_balances_location on public.inventory_balances(location_id);
create index idx_inventory_balances_product  on public.inventory_balances(product_id);


-- ─── 13. INVENTORY_MOVEMENTS ─────────────────────────────────────────────────
-- Log de movimentações de estoque (entrada, saída, transferência).
create table public.inventory_movements (
    id             uuid primary key default gen_random_uuid(),
    location_id    uuid not null references public.inventory_locations(id),
    product_id     uuid not null references public.products(id),
    movement_type  varchar(30) not null
                      check (movement_type in ('entrada_compra','saida_venda','transferencia','ajuste')),
    quantity       integer not null,
    reference_type varchar(30),   -- 'supply_order', 'sales_order', etc.
    reference_id   uuid,
    notes          text,
    created_by     uuid references public.users(id),
    created_at     timestamptz not null default now()
);
comment on table public.inventory_movements is 'Auditoria de todas as movimentações de estoque.';

create index idx_inventory_movements_location  on public.inventory_movements(location_id);
create index idx_inventory_movements_product   on public.inventory_movements(product_id);
create index idx_inventory_movements_reference on public.inventory_movements(reference_type, reference_id);


-- ─── 14. SUPPLY_ORDERS ───────────────────────────────────────────────────────
-- Pedidos de abastecimento B2B (parceiro compra da Hipnus).
create table public.supply_orders (
    id           uuid primary key default gen_random_uuid(),
    partner_id   uuid not null references public.partners(id) on delete restrict,
    status       varchar(20) not null default 'draft'
                    check (status in ('draft','placed','approved','picking','invoiced','shipped','delivered','canceled')),
    total_amount numeric(10,2) not null default 0,
    notes        text,
    created_at   timestamptz not null default now(),
    updated_at   timestamptz not null default now()
);
comment on table public.supply_orders is 'Pedidos de abastecimento B2B: parceiro compra produtos da Hipnus.';

create trigger trg_supply_orders_updated_at
  before update on public.supply_orders
  for each row execute function public.fn_set_updated_at();

create index idx_supply_orders_partner on public.supply_orders(partner_id);
create index idx_supply_orders_status  on public.supply_orders(status);


-- ─── 15. SUPPLY_ORDER_ITEMS ──────────────────────────────────────────────────
create table public.supply_order_items (
    id               uuid primary key default gen_random_uuid(),
    supply_order_id  uuid not null references public.supply_orders(id) on delete cascade,
    product_id       uuid not null references public.products(id) on delete restrict,
    quantity         integer not null check (quantity > 0),
    unit_price       numeric(10,2) not null,
    created_at       timestamptz not null default now()
);
comment on table public.supply_order_items is 'Itens de um pedido de abastecimento.';

create index idx_supply_order_items_order   on public.supply_order_items(supply_order_id);
create index idx_supply_order_items_product on public.supply_order_items(product_id);


-- ─── 16. SALES_ORDERS ────────────────────────────────────────────────────────
-- Pedidos de venda B2C (cliente compra da loja do parceiro).
create table public.sales_orders (
    id                   uuid primary key default gen_random_uuid(),
    store_id             uuid not null references public.stores(id) on delete restrict,
    customer_id          uuid not null references public.users(id) on delete restrict,
    address_id           uuid references public.addresses(id) on delete set null,
    channel              varchar(20) not null default 'online'
                            check (channel in ('online','physical')),
    status               varchar(20) not null default 'pending'
                            check (status in ('pending','paid','shipped','delivered','canceled','refunded','registered')),
    total_amount         numeric(10,2) not null default 0,
    floor_total          numeric(10,2) not null default 0,
    partner_margin_total numeric(10,2) not null default 0,
    notes                text,
    created_at           timestamptz not null default now(),
    updated_at           timestamptz not null default now()
);
comment on table public.sales_orders is 'Pedidos de venda B2C: cliente compra na loja do parceiro.';

create trigger trg_sales_orders_updated_at
  before update on public.sales_orders
  for each row execute function public.fn_set_updated_at();

create index idx_sales_orders_store    on public.sales_orders(store_id);
create index idx_sales_orders_customer on public.sales_orders(customer_id);
create index idx_sales_orders_status   on public.sales_orders(status);


-- ─── 17. SALES_ORDER_ITEMS ───────────────────────────────────────────────────
create table public.sales_order_items (
    id               uuid primary key default gen_random_uuid(),
    sales_order_id   uuid not null references public.sales_orders(id) on delete cascade,
    product_id       uuid not null references public.products(id) on delete restrict,
    product_name     varchar(255) not null,  -- snapshot no momento da compra
    quantity         integer not null check (quantity > 0),
    unit_floor_price numeric(10,2) not null,  -- snapshot
    unit_sale_price  numeric(10,2) not null,  -- snapshot
    created_at       timestamptz not null default now()
);
comment on table public.sales_order_items is 'Itens de um pedido de venda (snapshot de preços no momento da compra).';

create index idx_sales_order_items_order   on public.sales_order_items(sales_order_id);
create index idx_sales_order_items_product on public.sales_order_items(product_id);


-- ─── 18. PAYMENTS ────────────────────────────────────────────────────────────
-- Cobranças Asaas. Polimórfico: cobre sales_order e supply_order.
create table public.payments (
    id                 uuid primary key default gen_random_uuid(),
    order_type         varchar(20) not null
                          check (order_type in ('sales_order','supply_order')),
    order_id           uuid not null,
    asaas_payment_id   varchar(64) unique,
    asaas_customer_id  varchar(64),
    invoice_url        varchar(512),
    pix_qr_code        text,
    method             varchar(20) not null default 'UNDEFINED'
                          check (method in ('PIX','CREDIT_CARD','BOLETO','UNDEFINED')),
    status             varchar(20) not null default 'pending'
                          check (status in ('pending','confirmed','received','overdue','refunded','canceled')),
    amount             numeric(10,2) not null,
    paid_at            timestamptz,
    created_at         timestamptz not null default now(),
    updated_at         timestamptz not null default now()
);
comment on table public.payments is 'Cobranças Asaas (Pix/cartão/boleto) com split, para sales_order e supply_order.';

create trigger trg_payments_updated_at
  before update on public.payments
  for each row execute function public.fn_set_updated_at();

create index idx_payments_order      on public.payments(order_type, order_id);
create index idx_payments_asaas      on public.payments(asaas_payment_id);
create index idx_payments_status     on public.payments(status);


-- ─── 19. SHIPMENTS ───────────────────────────────────────────────────────────
-- Entregas/logística. Polimórfico: cobre sales_order e supply_order.
create table public.shipments (
    id             uuid primary key default gen_random_uuid(),
    order_type     varchar(20) not null
                      check (order_type in ('sales_order','supply_order')),
    order_id       uuid not null,
    status         varchar(20) not null default 'pending'
                      check (status in ('pending','picking','packed','shipped','in_transit','delivered','returned')),
    tracking_code  varchar(80),
    carrier        varchar(80),
    shipped_at     timestamptz,
    delivered_at   timestamptz,
    estimated_at   date,
    created_at     timestamptz not null default now(),
    updated_at     timestamptz not null default now()
);
comment on table public.shipments is 'Entregas e logística, tanto de pedidos de venda quanto de abastecimento.';

create trigger trg_shipments_updated_at
  before update on public.shipments
  for each row execute function public.fn_set_updated_at();

create index idx_shipments_order  on public.shipments(order_type, order_id);
create index idx_shipments_status on public.shipments(status);


-- ─── 20. COMMISSIONS ─────────────────────────────────────────────────────────
-- Registro do split financeiro de cada pedido de venda pago.
create table public.commissions (
    id              uuid primary key default gen_random_uuid(),
    sales_order_id  uuid not null unique references public.sales_orders(id) on delete cascade,
    hipnus_amount   numeric(10,2) not null,
    partner_amount  numeric(10,2) not null,
    platform_fee    numeric(10,2) not null default 0,
    asaas_split_id  varchar(64),
    created_at      timestamptz not null default now()
);
comment on table public.commissions is 'Resultado do split financeiro de cada venda paga (Hipnus x parceiro).';

create index idx_commissions_order on public.commissions(sales_order_id);


-- ─── 21. LOCATION CENTRAL PADRÃO ────────────────────────────────────────────
-- Garante que existe exatamente 1 local de estoque central
insert into public.inventory_locations (type, name)
values ('central', 'Armazém Central Hipnus');
