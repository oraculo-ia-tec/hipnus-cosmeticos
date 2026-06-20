"""
1_Catalogo.py — HIPNUS COSMÉTICOS
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from lib import api, ui
from lib.auth import require_auth, sidebar_logo
from lib import components, commerce

st.set_page_config(page_title="Catálogo · HIPNUS", page_icon="🛍️", layout="wide")
ui.inject_theme()
require_auth()
sidebar_logo()

all_products = api.get_products()
lines        = api.list_lines()
cats         = api.list_categories()

components.page_header(title="Catálogo de Produtos", subtitle=f"{len(all_products)} produtos · {len(lines)} linhas · {len(cats)} categorias")

col_s, col_l, col_c, col_k = st.columns([3, 2, 2, 1])
busca     = col_s.text_input("🔍 Buscar produto", placeholder="nome, linha…", label_visibility="collapsed")
linha_sel = col_l.selectbox("Linha",     ["Todas"] + lines, label_visibility="collapsed")
cat_sel   = col_c.selectbox("Categoria", ["Todas"] + cats,  label_visibility="collapsed")
so_kits   = col_k.checkbox("Kits", value=False)

products = all_products
if busca:
    q = busca.lower()
    products = [p for p in products if q in p["name"].lower() or q in (p.get("line") or "").lower()]
if linha_sel != "Todas":
    products = [p for p in products if p.get("line") == linha_sel]
if cat_sel != "Todas":
    products = [p for p in products if p.get("category") == cat_sel]
if so_kits:
    products = [p for p in products if p.get("is_kit")]

st.caption(f"{len(products)} produto(s) encontrado(s)")

if not products:
    components.empty_state(icon="🔍", title="Nenhum produto encontrado", message="Tente ajustar os filtros ou a busca.")
else:
    for i in range(0, len(products), 4):
        row = products[i:i+4]
        cols = st.columns(4)
        for col, p in zip(cols, row):
            with col:
                commerce.product_card(p, key_prefix="cat", on_add=ui.add_to_cart)
