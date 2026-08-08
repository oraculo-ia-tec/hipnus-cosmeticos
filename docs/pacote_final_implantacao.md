
# TÁLYA COSMÉTICOS — Pacote Final de Implantação

Este pacote organiza tudo que foi produzido para aplicação no repositório `oraculo-ia-tec/hipnus-cosmeticos` e no projeto Supabase.

---

## 1. Estrutura de destino no repositório

```text
hipnus-cosmeticos/
├── supabase/
│   ├── migrations/
│   │   ├── 001_schema.sql
│   │   ├── 002_rls_base.sql
│   │   ├── 003_rls_additions.sql
│   │   ├── 004_triggers.sql
│   │   ├── 005_views.sql
│   │   ├── 006_onboarding.sql
│   │   └── 007_store_theme.sql
│   └── functions/
│       ├── asaas-webhook/
│       │   └── index.ts
│       └── provision-asaas-partner/
│           └── index.ts
├── frontend/
│   ├── lib/
│   │   ├── queries.py
│   │   ├── onboarding_queries.py
│   │   └── theme_buttons.py
│   └── pages/
│       └── 11_🤝_Onboarding.py
└── docs/
    └── hipnus_apresentacao_paginas_perfis.html
```

---

## 2. Mapeamento dos arquivos gerados

| Arquivo gerado | Destino sugerido |
|---|---|
| `hipnus_schema_v2.sql` | `supabase/migrations/001_schema.sql` |
| `hipnus_rls_policies.sql` | `supabase/migrations/002_rls_base.sql` |
| `hipnus_rls_policies_v2_additions.sql` | `supabase/migrations/003_rls_additions.sql` |
| `hipnus_triggers_functions_v2.sql` | `supabase/migrations/004_triggers.sql` |
| `hipnus_views.sql` | `supabase/migrations/005_views.sql` |
| `hipnus_onboarding_schema.sql` | `supabase/migrations/006_onboarding.sql` |
| `hipnus_store_theme_schema.sql` | `supabase/migrations/007_store_theme.sql` |
| `asaas-webhook_index.ts` | `supabase/functions/asaas-webhook/index.ts` |
| `provision-asaas-partner_index.ts` | `supabase/functions/provision-asaas-partner/index.ts` |
| `streamlit_supabase_queries.py` | `frontend/lib/queries.py` |
| `hipnus_onboarding_queries.py` | `frontend/lib/onboarding_queries.py` |
| `streamlit_button_style_guide.py` | `frontend/lib/theme_buttons.py` |
| `streamlit_onboarding_and_store_config.py` | `frontend/pages/11_🤝_Onboarding.py` |
| `hipnus_apresentacao_paginas_perfis.html` | `docs/hipnus_apresentacao_paginas_perfis.html` |

---

## 3. Ordem de execução das migrations no Supabase

Execute nesta ordem:

1. `001_schema.sql`
2. `002_rls_base.sql`
3. `003_rls_additions.sql`
4. `004_triggers.sql`
5. `005_views.sql`
6. `006_onboarding.sql`
7. `007_store_theme.sql`

Motivo:
- o schema base cria tabelas principais;
- as policies dependem das tabelas e funções auxiliares;
- triggers dependem das tabelas e algumas funções RLS/base;
- views dependem das tabelas já criadas;
- onboarding e store theme são extensões do core.

---

## 4. Comandos Git sugeridos

```bash
git clone https://github.com/oraculo-ia-tec/hipnus-cosmeticos.git
cd hipnus-cosmeticos
git checkout -b feature/hipnus-supabase-onboarding-store

mkdir -p supabase/migrations
mkdir -p supabase/functions/asaas-webhook
mkdir -p supabase/functions/provision-asaas-partner
mkdir -p frontend/lib
mkdir -p frontend/pages
mkdir -p docs
```

Depois copie os arquivos para os destinos acima.

```bash
git add .
git commit -m "feat: supabase schema, onboarding de parceiros, edge functions Asaas e configuracao de loja"
git push origin feature/hipnus-supabase-onboarding-store
```

---

## 5. Deploy das Edge Functions

### Secrets necessários no Supabase

```bash
supabase secrets set ASAAS_API_KEY=... SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... ASAAS_BASE_URL=https://api.asaas.com/v3 ASAAS_WEBHOOK_TOKEN=...
```

### Deploy

```bash
supabase functions deploy provision-asaas-partner
supabase functions deploy asaas-webhook --no-verify-jwt
```

---

## 6. Integração no Streamlit

### Arquivos novos
- `frontend/lib/queries.py`
- `frontend/lib/onboarding_queries.py`
- `frontend/lib/theme_buttons.py`
- `frontend/pages/11_🤝_Onboarding.py`

### Configuração de secrets do Streamlit

Adicionar no `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "https://SEU-PROJETO.supabase.co"
SUPABASE_ANON_KEY = "SUA_CHAVE_ANON"
```

---

## 7. Checklist de validação pós-deploy

### Banco / Supabase
- [ ] Todas as 7 migrations executaram sem erro.
- [ ] Existe apenas 1 `inventory_location` com `type = 'central'`.
- [ ] Tabela `platform_settings` contém `platform_fee_rate`.
- [ ] RLS está ativo em todas as tabelas sensíveis.

### Auth / Usuários
- [ ] Login via Supabase Auth funciona.
- [ ] `public.users` está sincronizada com `auth.users`.
- [ ] Roles corretas: `admin`, `super_admin`, `distribuidor`, `salao`, `cliente`, `demo`.

### Onboarding
- [ ] Parceiro consegue se cadastrar.
- [ ] Admin visualiza parceiros pendentes.
- [ ] Aprovação muda `status` para `active`.
- [ ] Trigger cria `store` automaticamente.
- [ ] Trigger cria `inventory_location` da loja.

### Loja do parceiro
- [ ] Parceiro consegue configurar banner, logo e cores.
- [ ] Seções da vitrine aparecem na ordem correta.
- [ ] Preview da loja funciona no Streamlit.

### Compras e estoque
- [ ] Parceiro cria `supply_order` e envia pedido.
- [ ] Admin aprova e entrega pedido.
- [ ] Estoque central baixa corretamente.
- [ ] Estoque da loja recebe entrada corretamente.
- [ ] Cliente compra e estoque da loja baixa ao confirmar pagamento.

### Financeiro / Asaas
- [ ] Edge Function `provision-asaas-partner` cria subconta.
- [ ] Edge Function `asaas-webhook` atualiza `payments`.
- [ ] Trigger gera `commissions` automaticamente.
- [ ] `asaas_payment_id` não duplica eventos.

---

## 8. Testes ponta a ponta recomendados

### Cenário 1 — Onboarding completo
1. Criar usuário parceiro.
2. Enviar documentos.
3. Aprovar no admin.
4. Verificar criação automática da loja.
5. Provisionar Asaas.

### Cenário 2 — Abastecimento do parceiro
1. Parceiro acessa catálogo B2B.
2. Cria carrinho de abastecimento.
3. Finaliza pedido.
4. Admin aprova, separa e entrega.
5. Verificar movimentação de estoque central -> loja.

### Cenário 3 — Venda ao cliente final
1. Parceiro gera link de cadastro.
2. Cliente entra na loja vinculada.
3. Cliente compra.
4. Asaas confirma pagamento.
5. Verificar baixa no estoque da loja.
6. Verificar criação da comissão.

---

## 9. Próximo passo técnico sugerido

Depois da implantação, os próximos módulos prioritários são:
1. sincronização automática `auth.users -> public.users` via trigger ou webhook;
2. carrinho persistido no banco (`carts`, `cart_items`);
3. upload real de arquivos para Supabase Storage;
4. testes automatizados backend + integração;
5. dashboards analíticos por parceiro.
