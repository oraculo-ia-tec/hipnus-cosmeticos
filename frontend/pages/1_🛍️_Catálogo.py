"""
1_Catalogo.py — HIPNUS COSMÉTICOS
=====================================
Catálogo completo de produtos com filtros por linha, categoria e busca.

Acesso: qualquer perfil autenticado.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from lib import api, ui
from lib.auth import require_auth, sidebar_logo, sidebar_user_info, sidebar_logout_button
from lib import components, commerce

st.set_page_config(page_title="Catálogo · HIPNUS", page_icon="🛍️", layout="wide")
ui.inject_theme()
require_auth()

# ─ Sidebar: topo ────────────────────────────────────────────────────────
sidebar_logo()
sidebar_user_info()
ui.api_status_badge(api.api_online())

# ─ Carrinho flutuante ────────────────────────────────────────────────
ui.floating_cart_expander()

# ─ Dados ─────────────────────────────────────────────────────────────
all_products = api.get_products()
lines        = api.list_lines()
cats         = api.list_categories()

# ─ Header ────────────────────────────────────────────────────────────
components.page_header(
    title="Catálogo de Produtos",
    subtitle=f"{len(all_products)} produtos · {len(lines)} linhas · {len(cats)} categorias",
)

# ─ Filtros ───────────────────────────────────────────────────────────
col_s, col_l, col_c, col_k = st.columns([3, 2, 2, 1])
busca      = col_s.text_input("🔍 Buscar produto", placeholder="nome, linha…", label_visibility="collapsed")
linha_sel  = col_l.selectbox("Linha",     ["Todas"] + lines,  label_visibility="collapsed")
cat_sel    = col_c.selectbox("Categoria", ["Todas"] + cats,   label_visibility="collapsed")
so_kits    = col_k.checkbox("Kits", value=False)

# ─ Filtragem ─────────────────────────────────────────────────────────
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

# ─ Grid de produtos ──────────────────────────────────────────────────
if not products:
    components.empty_state(
        icon="🔍",
        title="Nenhum produto encontrado",
        message="Tente ajustar os filtros ou a busca.",
    )
else:
    cols_per_row = 4
    for i in range(0, len(products), cols_per_row):
        row = products[i : i + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, p in zip(cols, row):
            with col:
                commerce.product_card(p, key_prefix="cat", on_add=ui.add_to_cart)

# ─ Sidebar: rodapé ───────────────────────────────────────────────────────
st.sidebar.divider()
sidebar_logout_button()
