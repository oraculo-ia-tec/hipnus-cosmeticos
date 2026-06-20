"""
3_Loja_do_Parceiro.py — HIPNUS COSMÉTICOS
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from lib import api, ui
from lib.auth import require_auth, sidebar_logo, sidebar_user_info, sidebar_logout_button
from lib import components, commerce

st.set_page_config(page_title="Loja Parceiro · HIPNUS", page_icon="🏪", layout="wide")
ui.inject_theme()
require_auth(perfis_permitidos=["super_admin", "admin", "b2b"])
sidebar_logo()
sidebar_user_info()
sidebar_logout_button()

all_products = api.get_products()
lines        = api.list_lines()

components.page_header(title="Loja do Parceiro", subtitle="Condições exclusivas para profissionais, salões e distribuidores.", kicker="Área B2B")

linha_sel = st.selectbox("Filtrar por linha", ["Todas"] + lines, label_visibility="collapsed")
products  = all_products if linha_sel == "Todas" else [p for p in all_products if p.get("line") == linha_sel]
st.caption(f"{len(products)} produto(s)")
components.divider()

if not products:
    components.empty_state(icon="🏪", title="Nenhum produto encontrado", message="Tente ajustar o filtro de linha.")
else:
    for i in range(0, len(products), 4):
        row = products[i:i+4]
        cols = st.columns(4)
        for col, p in zip(cols, row):
            with col:
                commerce.product_card(p, key_prefix="b2b", on_add=ui.add_to_cart)
