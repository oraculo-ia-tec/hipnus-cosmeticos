
-- ============================================================
-- HIPNUS COSMETICOS - Extensao de Onboarding de Parceiros (v3)
-- ============================================================

-- 1. Dados bancarios/documentos para onboarding e Asaas
create table public.partner_onboarding (
    id uuid primary key default gen_random_uuid(),
    partner_id uuid not null unique references public.partners(id) on delete cascade,
    document_front_url text,
    document_back_url text,
    proof_of_address_url text,
    bank_name varchar(120),
    bank_agency varchar(20),
    bank_account varchar(30),
    bank_account_type varchar(20) check (bank_account_type in ('corrente','poupanca')),
    pix_key varchar(140),
    submitted_at timestamptz,
    reviewed_by uuid references public.users(id),
    reviewed_at timestamptz,
    rejection_reason text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
comment on table public.partner_onboarding is 'Dados complementares de onboarding: documentos, dados bancarios e trilha de aprovacao do parceiro.';

create trigger trg_partner_onboarding_updated_at before update on public.partner_onboarding
  for each row execute function public.fn_set_updated_at();

-- 2. Log de auditoria de mudanca de status do parceiro
create table public.partner_status_history (
    id uuid primary key default gen_random_uuid(),
    partner_id uuid not null references public.partners(id) on delete cascade,
    from_status varchar(20),
    to_status varchar(20) not null,
    changed_by uuid references public.users(id),
    reason text,
    created_at timestamptz not null default now()
);
comment on table public.partner_status_history is 'Auditoria de todas as mudancas de status do parceiro (pending -> active -> suspended -> rejected).';
create index idx_partner_status_history_partner on public.partner_status_history(partner_id);

-- 3. Trigger: ao aprovar parceiro (status -> active), criar loja automaticamente
create or replace function public.fn_partner_status_change()
returns trigger
language plpgsql
security definer
as $$
declare
  v_slug varchar(80);
  v_store_id uuid;
begin
  insert into public.partner_status_history (partner_id, from_status, to_status, changed_by)
  values (new.id, old.status, new.status, null);

  if new.status = 'active' and old.status != 'active' then

    if not exists (select 1 from public.stores where partner_id = new.id) then
      v_slug := lower(regexp_replace(new.name, '[^a-zA-Z0-9]+', '-', 'g')) || '-' || substr(new.id::text, 1, 6);

      insert into public.stores (partner_id, slug, display_name, is_active)
      values (new.id, v_slug, new.name, true)
      returning id into v_store_id;

      insert into public.inventory_locations (type, store_id, name)
      values ('store', v_store_id, new.name || ' - Estoque');
    end if;

  end if;

  return new;
end;
$$;

create trigger trg_partner_status_change
  after update of status on public.partners
  for each row
  execute function public.fn_partner_status_change();

comment on function public.fn_partner_status_change is
  'Ao aprovar parceiro (status=active): cria loja com slug unico e local de estoque automaticamente. Registra auditoria de status.';

-- 4. RLS
alter table public.partner_onboarding enable row level security;
alter table public.partner_status_history enable row level security;

create policy partner_onboarding_select on public.partner_onboarding
  for select using (
    public.is_admin()
    or partner_id = public.current_partner_id()
  );

create policy partner_onboarding_insert on public.partner_onboarding
  for insert with check (partner_id = public.current_partner_id());

create policy partner_onboarding_update on public.partner_onboarding
  for update using (
    public.is_admin()
    or (partner_id = public.current_partner_id() and reviewed_at is null)
  );

create policy partner_status_history_select on public.partner_status_history
  for select using (
    public.is_admin()
    or partner_id = public.current_partner_id()
  );
