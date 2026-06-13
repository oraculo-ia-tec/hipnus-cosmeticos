"""
Página de Linhas — navegação do portfólio por coleção/linha da marca.

Permite escolher uma linha (Turmalina, Ouro, Teia de Aranha, etc.) e ver
todos os produtos pertencentes a ela.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st  # noqa: E402

from lib import api, ui  # noqa: E402

st.set_page_config(page_title="Linhas · HIPNUS", page_icon="✨", layout="wide")
ui.inject_theme()

ui.brand_header()
ui.api_status_badge(api.api_online())
ui.sidebar_cart_summary()

products = api.get_products()
lines = api.list_lines()

st.markdown('<div class="hip-section-title">Linhas da marca</div>', unsafe_allow_html=True)
st.markdown('<div class="hip-section-sub">Escolha uma coleção para ver seus produtos.</div>',
            unsafe_allow_html=True)

selected = st.selectbox("Selecione uma linha", lines)

line_products = [p for p in products if p.get("line") == selected]
st.caption(f"{len(line_products)} produto(s) na linha {selected}.")

per_row = 4
for i in range(0, len(line_products), per_row):
    cols = st.columns(per_row)
    for col, p in zip(cols, line_products[i : i + per_row]):
        with col:
            ui.product_card(p, key_prefix="line")

st.markdown("---")
st.markdown('<div class="hip-section-sub">Produtos sem linha específica aparecem no '
            '<b>Catálogo</b> completo.</div>', unsafe_allow_html=True)
