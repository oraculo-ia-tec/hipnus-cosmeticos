
-- ============================================================
-- RLS adicional: platform_settings e addresses (v2)
-- ============================================================

alter table public.platform_settings enable row level security;

create policy platform_settings_select_all on public.platform_settings
  for select using (true);

create policy platform_settings_write_admin on public.platform_settings
  for all using (public.is_admin()) with check (public.is_admin());

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
