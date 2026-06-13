# Arquitetura — HIPNUS COSMÉTICOS

Marketplace proprietário da marca Hipnus Cosméticos. Cada **parceiro**
(profissional, salão, distribuidor, revendedor) abre uma **loja** com os
produtos oficiais da Hipnus e os comercializa online e fisicamente. O
pagamento online usa a **API oficial do Asaas** com **split** automático.

## Decisões de produto (confirmadas)

| Tema | Decisão |
|------|---------|
| Fluxo financeiro | **Asaas Split** com subcontas (wallets) por parceiro |
| Venda física | **Registro manual** (baixa de estoque + comissão), sem pagamento no sistema |
| Preço | **Piso** = tabela distribuidor 2026; parceiro define o preço de venda **≥ piso** |
| Entrega atual | Arquitetura + estrutura base (backend FastAPI + modelos + catálogo) |

## Stack

- **Backend:** FastAPI (Python) — API modular por domínios
- **ORM:** SQLAlchemy 2.0
- **Banco:** SQLite (local) → MySQL Hostinger (produção)
- **Integrações:** Asaas (pagamentos/split), SMTP Hostinger (e-mail), Groq (Hipnus AI)
- **Frontend:** Streamlit + Bootstrap 5 (próximo ciclo)
- **Ferramentas LLM:** FastAPI MCP (módulo `app/mcp`, próximo ciclo)

## Domínios (bounded contexts)

```
app/
├── core/            Config, exceções de domínio
├── db/              Engine, Base, mixins, registry de models
├── domains/
│   ├── catalog/     Produtos oficiais Hipnus (piso + preço sugerido)
│   ├── partners/    Onboarding de parceiros + provisionamento Asaas
│   ├── stores/      Lojas e ofertas (StoreListing com preço de venda)
│   ├── orders/      Pedidos, itens, comissões (split)
│   └── payments/    Cobranças Asaas + webhooks
├── integrations/
│   └── asaas/       Cliente HTTP + serviço de orquestração (split)
└── mcp/             Ferramentas MCP (futuro)
```

Cada domínio segue a mesma estrutura: `models/`, `schemas/`, `services/`,
`routers/`. A regra de negócio vive sempre na camada **service**; os routers
apenas orquestram I/O e documentam o contrato.

## Modelo de dados

```
Partner (1) ──── (1) Store (1) ──── (N) StoreListing (N) ──── (1) Product
   │                   │
   │ asaas_wallet_id   └── (1) ─── (N) Order ─── (N) OrderItem
   │ asaas_account_id                  │
   │                                   ├── (1) Payment   (Asaas)
   └──────────────────────────────────└── (1) Commission (split auditado)
```

- **Product.floor_price** — piso (tabela distribuidor), custo mínimo.
- **Product.suggested_retail_price** — sugestão de varejo (consumidor final).
- **StoreListing.sale_price** — preço do parceiro, validado `>= floor_price`.
- **OrderItem** guarda *snapshot* de piso e venda (auditoria/governança).
- **Commission** registra o resultado do split por pedido pago.

## Regra central de preço

```
StoreListing.sale_price >= Product.floor_price
margem_parceiro = sale_price - floor_price
```
Validada em `StoreService._validate_floor` → `PriceBelowFloorError` (HTTP 422).

## Split de pagamento (Asaas)

Para cada pedido pago (`AsaasService.compute_split`):

```
total        = Σ (sale_price  × qty)
floor_total  = Σ (floor_price × qty)
margem       = total − floor_total
taxa_plataforma = margem × HIPNUS_PLATFORM_FEE_PERCENT%
partner_amount  = margem − taxa_plataforma      # repassado via split (walletId)
hipnus_amount   = total − partner_amount         # retido na conta raiz
```

A cobrança é criada com `split: [{ walletId, fixedValue: partner_amount }]`.
O webhook do Asaas confirma o pagamento e dispara o registro da `Commission`.

## Onboarding de parceiro (subconta Asaas)

`POST /api/v1/partners` →
1. valida unicidade (e-mail, CPF/CNPJ)
2. cria `Partner` (PENDING)
3. `POST /accounts` no Asaas → recebe `id`, `walletId`, `apiKey`
4. persiste credenciais e marca `ACTIVE`
5. cria a `Store` 1:1

> A criação de subconta no Asaas exige conta raiz **PJ (CNPJ)**.
> O `apiKey` da subconta é retornado **uma única vez** e deve ser
> armazenado de forma segura (criptografado em produção).

## Contratos de API (v1)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET  | `/health` | Healthcheck |
| GET  | `/api/v1/catalog/products` | Lista produtos (filtros: category, line, search) |
| GET  | `/api/v1/catalog/products/{id}` | Detalhe do produto |
| POST | `/api/v1/catalog/products` | Cria produto (admin) |
| PATCH| `/api/v1/catalog/products/{id}` | Atualiza produto (admin) |
| POST | `/api/v1/partners` | Onboarding + subconta Asaas |
| GET  | `/api/v1/partners/{id}` | Detalhe do parceiro |
| GET  | `/api/v1/stores/{slug}` | Vitrine pública da loja |
| GET  | `/api/v1/stores/{id}/listings` | Ofertas da loja |
| POST | `/api/v1/stores/{id}/listings` | Adiciona produto à loja (valida piso) |
| PATCH| `/api/v1/stores/listings/{id}` | Atualiza oferta (valida piso) |
| POST | `/api/v1/payments/webhook` | Webhook de eventos Asaas |

## Catálogo (seed)

`data/catalog_seed.json` — **127 produtos**, **22 linhas**, **10 categorias**,
gerado a partir das tabelas oficiais (distribuidor + consumidor final 2026) e
do catálogo PDF da marca. Carregado via `python -m scripts.seed_catalog`.

## Roadmap dos próximos ciclos

1. **Orders/Checkout** — criação de pedido, cobrança Asaas com split, webhook → `PAID` + `Commission`.
2. **Auth** — JWT para painel do parceiro e área administrativa Hipnus.
3. **Frontend Streamlit** — vitrine B2C/B2B, painel do parceiro, checkout (templates `template-hipnus` + Bootstrap 5).
4. **MCP** — ferramentas FastAPI MCP (catálogo, pedidos) para copilotos Hipnus AI (Groq).
5. **Migrations** — Alembic para versionar o schema em produção (MySQL Hostinger).
6. **E-mail** — notificações transacionais via SMTP Hostinger (Hipnus Customers/Orders).
