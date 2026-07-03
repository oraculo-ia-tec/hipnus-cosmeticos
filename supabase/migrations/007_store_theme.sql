
-- ============================================================
-- HIPNUS COSMETICOS - Customizacao visual da Loja do Parceiro
-- ============================================================

create table public.store_themes (
    id uuid primary key default gen_random_uuid(),
    store_id uuid not null unique references public.stores(id) on delete cascade,
    banner_url text,
    logo_url text,
    primary_color varchar(9) default '#7c3aed',
    secondary_color varchar(9) default '#ec4899',
    background_style varchar(20) default 'light' check (background_style in ('light','dark')),
    tagline varchar(160),
    about_text text,
    whatsapp_number varchar(20),
    instagram_handle varchar(60),
    show_ratings boolean not null default true,
    highlight_line_id uuid references public.product_lines(id) on delete set null,
    updated_at timestamptz not null default now()
);
comment on table public.store_themes is 'Configuracao visual e institucional da loja do parceiro (identidade da vitrine).';

create trigger trg_store_themes_updated_at before update on public.store_themes
  for each row execute function public.fn_set_updated_at();

create table public.store_sections (
    id uuid primary key default gen_random_uuid(),
    store_id uuid not null references public.stores(id) on delete cascade,
    section_type varchar(30) not null check (section_type in ('banner','linha_destaque','depoimentos','sobre','combo','promocao')),
    title varchar(160),
    content text,
    image_url text,
    display_order integer not null default 0,
    is_active boolean not null default true,
    created_at timestamptz not null default now()
);
comment on table public.store_sections is 'Blocos configuraveis da vitrine (secoes reordenaveis pelo parceiro).';
create index idx_store_sections_store on public.store_sections(store_id, display_order);

alter table public.store_themes enable row level security;
alter table public.store_sections enable row level security;

create policy store_themes_select on public.store_themes
  for select using (true);

create policy store_themes_write_own on public.store_themes
  for all using (
    public.is_admin() or store_id = public.current_store_id()
  ) with check (
    public.is_admin() or store_id = public.current_store_id()
  );

create policy store_sections_select on public.store_sections
  for select using (is_active = true or public.is_admin() or store_id = public.current_store_id());

create policy store_sections_write_own on public.store_sections
  for all using (
    public.is_admin() or store_id = public.current_store_id()
  ) with check (
    public.is_admin() or store_id = public.current_store_id()
  );
