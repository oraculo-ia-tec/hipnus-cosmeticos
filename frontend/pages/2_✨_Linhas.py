"""
2_Linhas.py — HIPNUS COSMÉTICOS
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from lib import api, ui
from lib.auth import require_auth, sidebar_logo, sidebar_user_info, logout
from lib import components, commerce

st.set_page_config(page_title="Linhas · HIPNUS", page_icon="✨", layout="wide")
ui.inject_theme()
require_auth()
sidebar_logo()
sidebar_user_info()
if st.sidebar.button("🚶 Sair", use_container_width=True, key="logout_lin"):
    logout()

all_products = api.get_products()
lines        = api.list_lines()

components.page_header(title="Linhas da Marca", subtitle="Explore cada coleção desenvolvida pela Hipnus Cosméticos.")

if not lines:
    components.empty_state(icon="✨", title="Nenhuma linha encontrada", message="O catálogo ainda não possui linhas cadastradas.")
else:
    linha_sel = st.selectbox("Selecione a linha", lines)
    products  = [p for p in all_products if p.get("line") == linha_sel]
    st.caption(f"{len(products)} produto(s) na linha {linha_sel}")
    components.divider()
    if not products:
        components.empty_state(icon="📦", title=f"Nenhum produto na linha {linha_sel}", message="Esta linha ainda não possui produtos cadastrados.")
    else:
        for i in range(0, len(products), 4):
            row = products[i:i+4]
            cols = st.columns(4)
            for col, p in zip(cols, row):
                with col:
                    commerce.product_card(p, key_prefix="lin", on_add=ui.add_to_cart)
