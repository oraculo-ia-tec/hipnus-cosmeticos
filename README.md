# HIPNUS COSMÉTICOS

Marketplace proprietário da marca **Hipnus Cosméticos**. Cada parceiro
(profissional, salão, distribuidor ou revendedor) abre sua **loja** com os
produtos oficiais da Hipnus e os vende online e fisicamente. Pagamentos online
com **split automático** via **API oficial do Asaas**.

> Vitrine, compra e relacionamento direto com a Hipnus Cosméticos, em uma única
> plataforma para consumidor final e profissional.

## Principais conceitos

- **Catálogo único Hipnus** — 127 produtos, 22 linhas (Turmalina, Ouro, Teia de
  Aranha, Manga Rosa, Carbono Smooth Pro, Coffee Milk, Barber, etc.).
- **Piso de preço** — cada produto tem um `floor_price` (tabela distribuidor).
  O parceiro define o preço de venda **acima do piso** e fica com a margem.
- **Asaas Split** — cada parceiro é uma subconta (wallet) no Asaas; o pagamento
  é dividido automaticamente entre Hipnus e parceiro.
- **Venda física** — registrada manualmente (estoque + comissão), sem
  processar pagamento pelo sistema.

## Stack

FastAPI · SQLAlchemy 2.0 · SQLite (local) / MySQL (Hostinger) · Asaas ·
SMTP Hostinger · Groq (Hipnus AI) · Streamlit (frontend, próximo ciclo).

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
```

## Testes

```bash
pytest -q
```

## Estrutura

```
app/
├── core/          config, exceções
├── db/            engine, Base, mixins, registry
├── domains/       catalog · partners · stores · orders · payments
├── integrations/  asaas (client + service de split)
└── mcp/           ferramentas FastAPI MCP (futuro)
data/              catalog_seed.json + banco SQLite local
docs/              ARCHITECTURE.md
scripts/           seed_catalog.py
tests/             regras de negócio (piso, split)
```

Documentação completa de arquitetura, modelo de dados, contratos de API e
roadmap em [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Status

✅ Estrutura base: arquitetura, domínios, modelos, integração Asaas (contratos),
catálogo carregado, regras de preço/split testadas.
🔜 Próximo: checkout/pedidos, auth, frontend Streamlit, MCP, migrations.
