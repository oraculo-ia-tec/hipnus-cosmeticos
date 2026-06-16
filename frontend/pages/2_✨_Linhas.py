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

st.set_page_config(page_title="Linhas · HIPNUS", page_icon="✨", layout="wide")
ui.inject_theme()

require_auth()

# ─── Sidebar ───────────────────────────────────────────────────────────
ui.brand_header()                       # 1. Logo
sidebar_user_info()                     # 2. Usuário (ACIMA do menu)
# --- [menu nativo Streamlit aqui] ---
ui.api_status_badge(api.api_online())   # 4. Status API
ui.sidebar_cart_summary()               # 5. Carrinho
sidebar_logout_button()                 # 6. SAIR (ABAIXO do menu)

products = api.get_products()
lines    = api.list_lines()

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
