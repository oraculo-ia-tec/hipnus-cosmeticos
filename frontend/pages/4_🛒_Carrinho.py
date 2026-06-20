"""
4_Carrinho.py — HIPNUS COSMÉTICOS
Visuáliza e gerencia os itens do carrinho.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from lib import api, ui
from lib.auth import require_auth
from lib import components, commerce

st.set_page_config(page_title="Carrinho · HIPNUS", page_icon="🛒", layout="wide")
ui.inject_theme()
require_auth()

# ─ Conteúdo ───────────────────────────────────────────────────────────
components.page_header(
    title="Carrinho de Compras",
    subtitle="Revise os itens antes de finalizar o pedido.",
)

cart = ui._cart()
if not cart:
    components.empty_state(
        icon="🛒",
        title="Carrinho vazio",
        message="Adicione produtos pelo Catálogo ou pela Loja do Parceiro.",
    )
else:
    for item in list(cart.values()):
        c1, c2, c3, c4 = st.columns([4, 1, 2, 1])
        c1.markdown(f"**{item['name']}**")
        c2.markdown(f"`x{item['qty']}`")
        c3.markdown(f"`{ui.brl(item['price'] * item['qty'])}`")
        if c4.button("❌", key=f"rm_{item['id']}"):
            ui.remove_from_cart(item["id"])
            st.rerun()

    components.divider()
    commerce.cart_total_block(ui.cart_total())

    col_l, col_r = st.columns([1, 1])
    with col_l:
        if st.button("🗑️ Limpar carrinho", use_container_width=True):
            ui.clear_cart()
            st.rerun()
    with col_r:
        st.page_link("pages/5_💳_Checkout.py", label="→ Finalizar pedido", icon="💳")
