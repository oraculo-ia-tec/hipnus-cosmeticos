# Frontend — Vitrine HIPNUS COSMÉTICOS (Streamlit)

Vitrine multipágina da marca Hipnus, com visual clean/premium institucional.
Consome a API FastAPI do backend e funciona também em **modo demonstração**
(catálogo local) quando o backend não está no ar.

## Páginas

| Página | Arquivo | Descrição |
|--------|---------|-----------|
| Home / Vitrine | `Home.py` | Hero da marca, indicadores, linhas e destaques |
| Catálogo | `pages/1_🛍️_Catálogo.py` | Busca + filtros (categoria, linha, preço, kits) |
| Linhas | `pages/2_✨_Linhas.py` | Navegação por coleção da marca |
| Loja do Parceiro | `pages/3_🏪_Loja_do_Parceiro.py` | Vitrine pública por slug (via API) |
| Carrinho | `pages/4_🛒_Carrinho.py` | Itens, quantidades e total (checkout no próximo ciclo) |

## Estrutura

```
frontend/
├── Home.py              entrypoint
├── pages/               páginas adicionais (multipage Streamlit)
├── lib/
│   ├── config.py        URLs da API, paleta e identidade da marca
│   ├── api.py           cliente HTTP + fallback ao seed (offline)
│   └── ui.py            tema CSS, formatação BRL, card de produto, carrinho
└── .streamlit/config.toml
```

## Como rodar

```bash
pip install -r requirements.txt           # na raiz do projeto

# (opcional) suba o backend para dados reais e lojas de parceiros
uvicorn app.main:app --reload

# vitrine
streamlit run frontend/Home.py
# abre em http://localhost:8501
```

Variável de ambiente opcional:

- `HIPNUS_API_URL` — URL base do backend (default `http://localhost:8000`).

## Notas de design

- Paleta: roxo Hipnus (`#7C3AED`) + dourado (linha Ouro) sobre fundo claro.
- Preço exibido prioriza o **preço de varejo sugerido**; o **piso** do parceiro
  é mostrado como referência.
- Na **Loja do Parceiro**, o card usa o **preço de venda** definido pelo parceiro
  (sempre ≥ piso, validado no backend).
- O **checkout com split Asaas** será habilitado no próximo ciclo (módulo de
  pedidos). O botão "Finalizar compra" já está presente, desabilitado, sinalizando
  o roadmap.
