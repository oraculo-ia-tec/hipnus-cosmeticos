# Frontend — Vitrine HIPNUS COSMÉTICOS (Streamlit)

Vitrine multipágina da marca Hipnus, com visual clean/premium institucional.
Consume a API FastAPI do backend e funciona também em **modo demonstração**
(catálogo local) quando o backend não está no ar.

---

## Skills implementadas

### 🔐 Skill #1 — JWT Auto-Refresh (`lib/session_guard.py`)

Guardia de sessão com expiração automática.

- Sessão dura **8 horas** por padrão (`SESSION_DURATION_H`)
- Nos últimos **15 minutos**, exibe `@st.dialog` com contador regressivo
- Botão **Renovar Sessão** reseta o timestamp sem logout
- Sessão expirada → `@st.dialog` informativo + redirect para login
- Chamada: `check_session_expiry()` no topo de cada página autenticada

```python
from lib.session_guard import check_session_expiry
check_session_expiry()
```

---

### 📧 Skill #2 — SMTP Centralizado (`lib/email_service.py`)

Engine de e-mail único via SMTP SSL Hostinger (porta 465).

```python
from lib.email_service import smtp_status, send_test_email, send_invite_email

# Diagnóstico
ok = smtp_status()["ready"]

# Teste manual
send_test_email("admin@empresa.com")

# Convite de parceiro
send_invite_email(destinatario, signup_url, role="b2b")
```

Variáveis de ambiente (ou Streamlit Secrets):

```
SMTP_HOST     smtp.hostinger.com
SMTP_PORT     465
SMTP_USER     no-reply@hipnuscosmeticos.com.br
SMTP_PASSWORD ...
SMTP_FROM     no-reply@hipnuscosmeticos.com.br
```

---

### 📧 Skill #3 — Confirmação de Pedido (`lib/email_service.py`)

Disparo automático de e-mail transacional após checkout bem-sucedido.

```python
from lib.email_service import send_order_confirmation_email

ok, msg = send_order_confirmation_email(
    to_email=email_cliente,
    customer_name=nome_cliente,
    billing_type="PIX",        # ou "BOLETO"
    resultado=resultado,       # dict de CheckoutService.processar()
    itens=list(cart.values()), # itens do carrinho
)
```

Template HTML inclui: tabela de itens, total BRL, referência, ID Asaas,
método de pagamento, status e botão CTA para link de pagamento.

---

### 📊 Skill #4 — Dashboard Admin (`pages/0_📊_Dashboard.py`)

Painel operacional exclusivo para `super_admin` e `admin`.

**KPIs financeiros** (via `AsaasClient.list_payments()`):
- Total Recebido / Pendente / Vencido — valor BRL + contagem
- Total de cobranças no período selecionado

**KPIs de plataforma** (banco local):
- Parceiros cadastrados
- Convites ativos / usados / totais

**Tabs de detalhe:** Cobranças · Convites · Parceiros · Sessão

Filtro de período: 7, 15, 30, 60 ou 90 dias. Cache em `session_state`.
Degradação graciosa se `ASAAS_API_KEY` não estiver configurada.

---

### 🤖 Skill #5 — IA Consultora (`lib/ia_consultora.py`)

Chat inteligente com contexto real da plataforma via Groq.

```python
from lib.ia_consultora import build_context, chat_stream, groq_status

# Verifica se a chave está configurada
if groq_status()["configured"]:
    ctx = build_context(usuario, cart, historico_pedidos, smtp_ok)
    for chunk in chat_stream(messages, ctx):
        st.write(chunk)  # streaming
```

**Modelo:** `llama-3.3-70b-versatile` via `api.groq.com/openai/v1`

**Contexto injetado a cada mensagem:**
- Usuário logado (nome, perfil, e-mail)
- Itens e total do carrinho atual
- Últimos 5 pedidos da sessão (ref, status, valor)
- Status do SMTP

**Secret necessário:** `GROQ_API_KEY = "gsk_..."`

**Dependência:** `openai>=1.0.0` (já no `requirements.txt`)

---

## Páginas

| # | Página | Arquivo | Descrição |
|---|--------|---------|------------|
| 0 | Dashboard Admin | `0_📊_Dashboard.py` | KPIs, cobranças, convites, parceiros |
| 1 | Home / Vitrine | `0_🏠_Home.py` | Hero, indicadores, linhas e destaques |
| 2 | Catálogo | `1_🛒_Catálogo.py` | Busca + filtros por categoria, linha, preço |
| 3 | Linhas | `2_💩_Linhas.py` | Navegação por coleção |
| 4 | Loja do Parceiro | `3_🏪_Loja_Parceiro.py` | Vitrine pública por slug |
| 5 | Carrinho | `4_🛒_Carrinho.py` | Itens, quantidades, total |
| 6 | Checkout | `5_💳_Checkout.py` | PIX / Boleto via Asaas + e-mail de confirmação |
| 7 | Convites | `6_✉️_Convites.py` | Criação e disparo de convites de parceiro |
| 8 | Cadastro Parceiro | `7_🤝_Cadastro_Parceiro.py` | Onboarding via convite |
| 9 | Configurações | `8_⚙️_Configuração.py` | Perfil, SMTP, Asaas, parceiro |
| 10 | IA Consultora | `10_🤖_IA_Consultora.py` | Chat Groq com contexto da plataforma |

---

## Estrutura da `lib/`

```
lib/
├── api.py              cliente HTTP + fallback offline
├── asaas_client.py     AsaasClient + AsaasService + list_payments()
├── auth.py             require_auth(), _gravar_sessao(), logout()
├── checkout_service.py orquestra checkout Asaas (calcular, registrar, processar)
├── commerce.py         product_card(), cart_row(), cart_total_block()
├── components.py       page_header(), section_title(), feedback_inline(), empty_state()
├── config.py           URLs da API, paleta e identidade da marca
├── db_utils.py         helpers SQLite
├── email_service.py    smtp_status() · send_email() · send_test_email()
│                       send_invite_email() · send_order_confirmation_email()
├── ia_consultora.py    groq_status() · build_context() · chat_stream()
├── invite_db.py        CRUD de convites (SQLite)
├── session_guard.py    check_session_expiry() · iniciar_sessao()
├── theme.py            CSS tokens + inject_theme()
├── tokens.py           design tokens (cores, espaçamentos)
├── ui.py               brl(), cart helpers, sidebar_cart_summary()
└── user_db.py          CRUD de usuários e parceiros (SQLite)
```

---

## Como rodar

```bash
pip install -r requirements.txt
streamlit run frontend/Home.py
# http://localhost:8501
```

Variáveis opcionais (`.env` ou `.streamlit/secrets.toml`):

```
HIPNUS_API_URL       http://localhost:8000
ASAAS_API_KEY        $aact_...
ASAAS_BASE_URL       https://api-sandbox.asaas.com/v3
PARTNER_WALLET_ID    (walletId subconta parceiro)
SMTP_HOST            smtp.hostinger.com
SMTP_PORT            465
SMTP_USER            no-reply@hipnuscosmeticos.com.br
SMTP_PASSWORD        ...
SMTP_FROM            no-reply@hipnuscosmeticos.com.br
GROQ_API_KEY         gsk_...
```

---

## Notas de design

- Paleta: roxo Hipnus (`#7C3AED`) + dourado (linha Ouro) sobre fundo claro.
- Preço exibido prioriza o **preço de varejo sugerido**; o **piso** do parceiro
  é mostrado como referência.
- Na **Loja do Parceiro**, o card usa o **preço de venda** definido pelo parceiro
  (sempre ≥ piso, validado no backend).
- O **split Asaas** é calculado em `CheckoutService.calcular_totais()` e
  aplicado automaticamente em `create_charge_with_split()`.
