"""
3_Loja_do_Parceiro.py — HIPNUS COSMÉTICOS
Vitrine personalizada para parceiros B2B.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from lib import api, ui
from lib.auth import require_auth
from lib import components, commerce

st.set_page_config(page_title="Loja Parceiro · HIPNUS", page_icon="🏪", layout="wide")
ui.inject_theme()
require_auth(perfis_permitidos=["super_admin", "admin", "b2b"])

# ─ Dados ─────────────────────────────────────────────────────────────
all_products = api.get_products()
lines        = api.list_lines()

# ─ Header ────────────────────────────────────────────────────────────
components.page_header(
    title="Loja do Parceiro",
    subtitle="Condições exclusivas para profissionais, salões e distribuidores.",
    kicker="Área B2B",
)

# ─ Filtro de linha ───────────────────────────────────────────────────
linha_sel = st.selectbox("Filtrar por linha", ["Todas"] + lines, label_visibility="collapsed")
products  = all_products if linha_sel == "Todas" else [
    p for p in all_products if p.get("line") == linha_sel
]
st.caption(f"{len(products)} produto(s)")
components.divider()

# ─ Grid de produtos ──────────────────────────────────
if not products:
    components.empty_state(
        icon="🏪",
        title="Nenhum produto encontrado",
        message="Tente ajustar o filtro de linha.",
    )
else:
    cols_per_row = 4
    for i in range(0, len(products), cols_per_row):
        row = products[i : i + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, p in zip(cols, row):
            with col:
                commerce.product_card(p, key_prefix="b2b", on_add=ui.add_to_cart)
