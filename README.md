# HIPNUS COSMÉTICOS

Marketplace proprietário da marca **Hipnus Cosméticos**. Cada parceiro
(profissional, salão, distribuidor ou revendedor) abre sua **loja** com os
produtos oficiais da Hipnus e os vende online e fisicamente. Pagamentos online
com **split automático** via **API oficial do Asaas**.

> Vitrine, compra e relacionamento direto com a Hipnus Cosméticos, em uma única
> plataforma para consumidor final e profissional.

---

## Skills entregues

| # | Skill | Arquivos principais | O que faz |
|---|---|---|---|
| 1 | 🔐 **JWT Auto-Refresh** | `lib/session_guard.py` | Controla expiração de sessão (8h), exibe aviso nos últimos 15 min via `st.dialog` e oferece renovação sem logout |
| 2 | 📧 **SMTP Centralizado** | `lib/email_service.py` | Engine SSL único via Hostinger (porta 465); exporta `smtp_status`, `send_test_email` e `send_invite_email` |
| 3 | 📧 **Confirmação de Pedido** | `lib/email_service.py` | `send_order_confirmation_email()` disparada automaticamente no checkout com template HTML, tabela de itens e link de pagamento |
| 4 | 📊 **Dashboard Admin** | `pages/0_📊_Dashboard.py` | Painel exclusivo para admin com 8 KPIs (cobranças Asaas, convites, parceiros), 4 tabs de detalhe e seletor de período |
| 5 | 🤖 **IA Consultora** | `lib/ia_consultora.py`, `pages/10_🤖_IA_Consultora.py` | Chat com Groq (Llama 3.3 70B), contexto dinâmico da sessão, streaming, 6 prompts rápidos e histórico |

---

## Principais conceitos

- **Catálogo único Hipnus** — 127 produtos, 22 linhas (Turmalina, Ouro, Teia de
  Aranha, Manga Rosa, Carbono Smooth Pro, Coffee Milk, Barber, etc.).
- **Piso de preço** — cada produto tem um `floor_price` (tabela distribuidor).
  O parceiro define o preço de venda **acima do piso** e fica com a margem.
- **Asaas Split** — cada parceiro é uma subconta (wallet) no Asaas; o pagamento
  é dividido automaticamente entre Hipnus e parceiro.
- **Venda física** — registrada manualmente (estoque + comissão), sem
  processar pagamento pelo sistema.

---

## Stack

FastAPI · SQLAlchemy 2.0 · SQLite (local) / MySQL (Hostinger) · Asaas ·
SMTP Hostinger · Groq / Llama 3.3 70B · Streamlit · OpenAI SDK (Groq-compat).

---

## Secrets necessários (`.streamlit/secrets.toml`)

```toml
# Asaas
ASAAS_API_KEY        = "$aact_..."
ASAAS_BASE_URL       = "https://api-sandbox.asaas.com/v3"
PARTNER_WALLET_ID    = ""          # walletId da subconta do parceiro

# SMTP Hostinger
SMTP_HOST            = "smtp.hostinger.com"
SMTP_PORT            = "465"
SMTP_USER            = "no-reply@hipnuscosmeticos.com.br"
SMTP_PASSWORD        = "..."
SMTP_FROM            = "no-reply@hipnuscosmeticos.com.br"

# IA Consultora
GROQ_API_KEY         = "gsk_..."
```

---

## Como rodar (local)

```bash
# 1. Ambiente
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configuração
cp .env.example .env        # preencha ASAAS_API_KEY etc.

# 3. Seed do catálogo Hipnus
python -m scripts.seed_catalog

# 4. Subir a API
uvicorn app.main:app --reload
# Docs interativas: http://localhost:8000/docs

# 5. Subir a vitrine (frontend Streamlit)
streamlit run frontend/Home.py
# Vitrine: http://localhost:8501
```

> A vitrine funciona mesmo sem o backend no ar (modo demonstração com catálogo
> local). Detalhes em [`frontend/README.md`](frontend/README.md).

---

## Testes

```bash
pytest -q
```

---

## Estrutura

```
app/
├── core/          config, exceções
├── db/            engine, Base, mixins, registry
├── domains/       catalog · partners · stores · orders · payments
├── integrations/  asaas (client + service de split)
└── mcp/           ferramentas FastAPI MCP (futuro)
frontend/
├── Home.py
├── pages/
│   ├── 0_📊_Dashboard.py     ← Skill #4
│   ├── 1_🛒_Catálogo.py
│   ├── 5_💳_Checkout.py      ← Skill #3 (e-mail pós-compra)
│   ├── 6_✉️_Convites.py      ← Skill #2 (convite automático)
│   └── 10_🤖_IA_Consultora.py ← Skill #5
├── lib/
│   ├── asaas_client.py      list_payments() + split
│   ├── auth.py              JWT sessão + require_auth()
│   ├── checkout_service.py  orquestra checkout Asaas
│   ├── commerce.py          cards, carrinho, preços
│   ├── components.py        UI atoms (header, divider, feedback)
│   ├── email_service.py     SMTP + todos os templates  ← Skills #2 e #3
│   ├── ia_consultora.py     Groq chat + build_context()  ← Skill #5
│   ├── invite_db.py         CRUD de convites
│   ├── session_guard.py     JWT auto-refresh  ← Skill #1
│   ├── theme.py             tokens CSS + inject_theme()
│   ├── tokens.py            design tokens
│   ├── ui.py                helpers de UI (BRL, cart, sidebar)
│   └── user_db.py           CRUD de usuários e parceiros
data/              catalog_seed.json + banco SQLite local
docs/              ARCHITECTURE.md
scripts/           seed_catalog.py
tests/             regras de negócio (piso, split)
```

---

## Status

✅ Backend: arquitetura, domínios, modelos, integração Asaas (contratos),
catálogo carregado, regras de preço/split testadas.

✅ Frontend: vitrine Streamlit completa com checkout Asaas, split, PIX/Boleto.

✅ Skills entregues: JWT Auto-Refresh · SMTP centralizado · Confirmação de pedido
· Dashboard Admin · IA Consultora (Groq).

🔜 Próximo: IA Consultora Abordagem B (RAG com dados reais) · migrations Alembic · MCP tools.
