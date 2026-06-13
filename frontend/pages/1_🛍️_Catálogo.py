"""
Página de Catálogo — todos os produtos Hipnus com busca e filtros.

Filtros: termo de busca (nome), categoria, linha, faixa de preço e
"apenas kits". A grade exibe cards de produto com adição ao carrinho.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st  # noqa: E402

from lib import api, ui  # noqa: E402

st.set_page_config(page_title="Catálogo · HIPNUS", page_icon="🛍️", layout="wide")
ui.inject_theme()

ui.brand_header()
ui.api_status_badge(api.api_online())
ui.sidebar_cart_summary()

products = api.get_products()

st.markdown('<div class="hip-section-title">Catálogo Hipnus</div>', unsafe_allow_html=True)
st.markdown('<div class="hip-section-sub">Todo o portfólio da marca em um só lugar.</div>',
            unsafe_allow_html=True)

# ------------------------------------------------------------------- filtros
f1, f2, f3 = st.columns([2, 1.3, 1.3])
search = f1.text_input("Buscar produto", placeholder="Ex.: máscara, ouro, progressiva...")
category = f2.selectbox("Categoria", ["Todas"] + api.list_categories())
line = f3.selectbox("Linha", ["Todas"] + api.list_lines())

prices = [float(p.get("suggested_retail_price") or p.get("floor_price") or 0) for p in products]
max_price = max(prices) if prices else 500.0
g1, g2 = st.columns([3, 1])
price_range = g1.slider("Faixa de preço (referência)", 0.0, float(round(max_price + 10)),
                        (0.0, float(round(max_price + 10))), step=5.0)
only_kits = g2.checkbox("Apenas kits")

# ------------------------------------------------------------------- aplica
def _matches(p: dict) -> bool:
    price = float(p.get("suggested_retail_price") or p.get("floor_price") or 0)
    if search and search.lower() not in p["name"].lower():
        return False
    if category != "Todas" and p.get("category") != category:
        return False
    if line != "Todas" and p.get("line") != line:
        return False
    if not (price_range[0] <= price <= price_range[1]):
        return False
    if only_kits and not p.get("is_kit"):
        return False
    return True

results = [p for p in products if _matches(p)]
st.caption(f"{len(results)} produto(s) encontrado(s).")

# --------------------------------------------------------------------- grade
if not results:
    st.info("Nenhum produto corresponde aos filtros selecionados.")
else:
    per_row = 4
    for i in range(0, len(results), per_row):
        cols = st.columns(per_row)
        for col, p in zip(cols, results[i : i + per_row]):
            with col:
                ui.product_card(p, key_prefix="cat")
