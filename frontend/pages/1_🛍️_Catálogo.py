"""
1_Catálogo.py — HIPNUS COSMÉTICOS
===================================
Página de Catálogo — todos os produtos Hipnus com busca e filtros.

Filtros: termo de busca (nome), categoria, linha, faixa de preço e
"apenas kits". A grade exibe cards de produto com adição ao carrinho.

Ordem da sidebar:
  1. brand_header()
  2. sidebar_user_info()      ← ACIMA do menu
  3. [menu nativo]
  4. api_status_badge()
  5. sidebar_cart_summary()
  6. sidebar_logout_button()  ← ABAIXO do menu
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from lib import api, ui
from lib.auth import require_auth, sidebar_user_info, sidebar_logout_button

st.set_page_config(page_title="Catálogo · HIPNUS", page_icon="🛍️", layout="wide")
ui.inject_theme()

require_auth()

# ─── Sidebar ───────────────────────────────────────────────────────────
ui.brand_header()                       # 1. Logo
sidebar_user_info()                     # 2. Usuário (ACIMA do menu)
# --- [menu nativo Streamlit aqui] ---
ui.api_status_badge(api.api_online())   # 4. Status API
ui.sidebar_cart_summary()               # 5. Carrinho
sidebar_logout_button()                 # 6. SAIR (ABAIXO do menu)

products = api.get_products()

st.markdown('<div class="hip-section-title">Catálogo Hipnus</div>', unsafe_allow_html=True)
st.markdown('<div class="hip-section-sub">Todo o portfólio da marca em um só lugar.</div>',
            unsafe_allow_html=True)

# ------------------------------------------------------------------- filtros
f1, f2, f3 = st.columns([2, 1.3, 1.3])
search   = f1.text_input("Buscar produto", placeholder="Ex.: máscara, ouro, progressiva...")
category = f2.selectbox("Categoria", ["Todas"] + api.list_categories())
line     = f3.selectbox("Linha", ["Todas"] + api.list_lines())

prices    = [float(p.get("suggested_retail_price") or p.get("floor_price") or 0) for p in products]
max_price = max(prices) if prices else 500.0
g1, g2   = st.columns([3, 1])
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
