"""
4_Carrinho.py — HIPNUS COSMÉTICOS
===================================
Revisão de itens, quantidades e total.
O botão de checkout redireciona para a página de pagamento.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from lib import api, ui
from lib.auth import require_auth, sidebar_user_info, sidebar_logout_button
from lib import components, commerce

st.set_page_config(page_title="Carrinho · HIPNUS", page_icon="🛒", layout="wide")
ui.inject_theme()

require_auth()

# ─ Sidebar ───────────────────────────────────────────────────────────
ui.brand_header()
sidebar_user_info()
ui.api_status_badge(api.api_online())
ui.sidebar_cart_summary()
sidebar_logout_button()

# ─ Cabeçalho ─────────────────────────────────────────────────────────
components.section_title("Seu carrinho")

cart = st.session_state.get("cart", {})

# ─ Estado vazio ──────────────────────────────────────────────────────
if not cart:
    clicked = components.empty_state(
        icon="🛒",
        title="Seu carrinho está vazio",
        message="Adicione produtos no catálogo para começar.",
        action_label="Ir para o catálogo",
        action_key="empty_cart_go_catalog",
    )
    if clicked:
        st.switch_page("pages/1_🛍️_Catálogo.py")

else:
    # ─ Cabeçalho da tabela ───────────────────────────────────────────
    h = st.columns([4, 1.4, 1.4, 1.6, 0.6])
    for col, label in zip(h, ["Produto", "Preço", "Qtd", "Subtotal", ""]):
        col.markdown(f"**{label}**")

    # ─ Linhas do carrinho ────────────────────────────────────────────
    for item in list(cart.values()):
        result = commerce.cart_row(item, cart=cart)
        if result is not None:
            if result == 0:
                st.rerun()
            else:
                cart[item["id"]]["qty"] = result
                st.rerun()

    components.divider()

    left, right = st.columns([3, 1.5])

    with right:
        go_checkout = commerce.cart_total_block(
            total=ui.cart_total(),
            key_checkout="go_checkout",
        )
        if go_checkout:
            st.switch_page("pages/5_Checkout.py")

    with left:
        with st.popover("ℹ️ Como funciona o pagamento?", use_container_width=False):
            st.markdown(
                "O pagamento é processado via **Asaas** com split automático: "
                "o piso (floor_price) fica na Hipnus e a margem é repassada ao parceiro."
            )
