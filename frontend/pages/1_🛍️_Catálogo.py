"""
1_Catálogo.py — HIPNUS COSMÉTICOS
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from lib import api, ui
from lib.auth import require_auth, build_sidebar
from lib import components, commerce

st.set_page_config(page_title="Catálogo · HIPNUS", page_icon="🛍️", layout="wide")
ui.inject_theme()
require_auth()
build_sidebar()

all_products = api.get_products()
lines        = api.list_lines()
cats         = api.list_categories()

components.page_header(title="Catálogo", subtitle="Todos os produtos Hipnus Cosméticos.")

col_f1, col_f2 = st.columns([2, 1])
with col_f1:
    linha_sel = st.selectbox("Linha", ["— Todas —"] + lines, key="cat_linha")
with col_f2:
    cat_sel = st.selectbox("Categoria", ["— Todas —"] + cats, key="cat_cat")

products = all_products
if linha_sel != "— Todas —":
    products = [p for p in products if p.get("line") == linha_sel]
if cat_sel != "— Todas —":
    products = [p for p in products if p.get("category") == cat_sel]

st.caption(f"{len(products)} produto(s) encontrado(s)")
components.divider()

if not products:
    components.empty_state(icon="🛍️", title="Nenhum produto encontrado", message="Ajuste os filtros acima.")
else:
    for i in range(0, len(products), 4):
        row = products[i:i+4]
        cols = st.columns(4)
        for col, p in zip(cols, row):
            with col:
                commerce.product_card(p, key_prefix="cat", on_add=ui.add_to_cart)
