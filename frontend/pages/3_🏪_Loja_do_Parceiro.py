"""
3_Loja_do_Parceiro.py — HIPNUS COSMÉTICOS
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from lib import api, ui
from lib.auth import require_auth, build_sidebar
from lib import components, commerce

st.set_page_config(page_title="Loja Parceiro · HIPNUS", page_icon="🏪", layout="wide")
ui.inject_theme()
require_auth(perfis_permitidos=["super_admin", "admin", "b2b"])
build_sidebar()

all_products = api.get_products()

components.page_header(title="Loja do Parceiro", subtitle="Preços e condições exclusivos para profissionais B2B.")

if not all_products:
    components.empty_state(icon="🏪", title="Nenhum produto disponível", message="O catálogo ainda não possui produtos cadastrados.")
else:
    for i in range(0, len(all_products), 4):
        row = all_products[i:i+4]
        cols = st.columns(4)
        for col, p in zip(cols, row):
            with col:
                commerce.product_card(p, key_prefix="loja", on_add=ui.add_to_cart)
