"""
2_Linhas.py — HIPNUS COSMÉTICOS
=================================
Página de Linhas — navegação do portfólio por coleção/linha da marca.

Permite escolher uma linha (Turmalina, Ouro, Teia de Aranha, etc.) e ver
todos os produtos pertencentes a ela.

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
from lib import components, commerce

st.set_page_config(page_title="Linhas · HIPNUS", page_icon="✨", layout="wide")
ui.inject_theme()

require_auth()

# ─ Sidebar ───────────────────────────────────────────────────────────
ui.brand_header()
sidebar_user_info()
ui.api_status_badge(api.api_online())
ui.sidebar_cart_summary()
sidebar_logout_button()

# ─ Dados ─────────────────────────────────────────────────────────────
products = api.get_products()
lines    = api.list_lines()

# ─ Cabeçalho ─────────────────────────────────────────────────────────
components.page_header(
    title="Linhas da marca",
    subtitle="Explore cada coleção e os produtos que a compõem.",
    kicker="Portfólio Hipnus",
)

# ─ Seletor de linha ───────────────────────────────────────────────────
selected = st.selectbox("Selecione uma linha", lines)

line_products = [p for p in products if p.get("line") == selected]

st.caption(f"{len(line_products)} produto(s) na linha **{selected}**.")

components.divider()

# ─ Grid de produtos ───────────────────────────────────────────────────
if not line_products:
    components.empty_state(
        icon="✨",
        title="Nenhum produto nesta linha",
        message="Esta linha ainda não possui produtos cadastrados no catálogo.",
    )
else:
    per_row = 4
    for i in range(0, len(line_products), per_row):
        cols = st.columns(per_row)
        for col, p in zip(cols, line_products[i : i + per_row]):
            with col:
                commerce.product_card(p, key_prefix="line", on_add=ui.add_to_cart)

components.divider()

with st.popover("ℹ️ Sobre o catálogo", use_container_width=False):
    st.markdown(
        "Produtos sem linha específica aparecem no **Catálogo** completo. "
        "Use o menu lateral para navegar entre as seções."
    )
