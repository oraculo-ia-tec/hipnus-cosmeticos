"""
2_Linhas.py — HIPNUS COSMÉTICOS
=====================================
Explore as linhas de produtos da marca Hipnus.

Acesso: qualquer perfil autenticado.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from lib import api, ui
from lib.auth import require_auth, sidebar_logo, sidebar_user_info, sidebar_logout_button
from lib import components, commerce

st.set_page_config(page_title="Linhas · HIPNUS", page_icon="✨", layout="wide")
ui.inject_theme()
require_auth()

# ─ Sidebar ───────────────────────────────────────────────────────────
sidebar_logo()
sidebar_user_info()
ui.api_status_badge(api.api_online())
sidebar_logout_button()

# ─ Carrinho flutuante ────────────────────────────────────────────────
ui.floating_cart_expander()

# ─ Dados ─────────────────────────────────────────────────────────────
all_products = api.get_products()
lines        = api.list_lines()

# ─ Header ────────────────────────────────────────────────────────────
components.page_header(
    title="Linhas da Marca",
    subtitle="Explore cada coleção desenvolvida pela Hipnus Cosméticos.",
)

# ─ Navegação por linha ───────────────────────────────────────────────
if not lines:
    components.empty_state(
        icon="✨",
        title="Nenhuma linha encontrada",
        message="O catálogo ainda não possui linhas cadastradas.",
    )
else:
    linha_sel = st.selectbox("Selecione a linha", lines)
    products  = [p for p in all_products if p.get("line") == linha_sel]
    st.caption(f"{len(products)} produto(s) na linha {linha_sel}")
    components.divider()

    if not products:
        components.empty_state(
            icon="📦",
            title=f"Nenhum produto na linha {linha_sel}",
            message="Esta linha ainda não possui produtos cadastrados.",
        )
    else:
        cols_per_row = 4
        for i in range(0, len(products), cols_per_row):
            row = products[i : i + cols_per_row]
            cols = st.columns(cols_per_row)
            for col, p in zip(cols, row):
                with col:
                    commerce.product_card(p, key_prefix="lin", on_add=ui.add_to_cart)
