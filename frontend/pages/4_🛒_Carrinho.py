"""
4_Carrinho.py — HIPNUS COSMÉTICOS
Carrinho com controles +/- por item.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from lib import api, ui
from lib.auth import sidebar_logo, sidebar_user_info, sidebar_logout_button
from lib.page_guard import guard
from lib import components, commerce
from lib.cart_widget import floating_cart

st.set_page_config(page_title="Carrinho · HIPNUS", page_icon="🛒", layout="wide")
ui.inject_theme()
guard("carrinho")
sidebar_logo()
sidebar_user_info()
sidebar_logout_button()
floating_cart()

components.page_header(title="Carrinho de Compras", subtitle="Revise os itens antes de finalizar o pedido.")

cart = ui._cart()
if not cart:
    components.empty_state(
        icon="🛒",
        title="Carrinho vazio",
        message="Adicione produtos pelo Catálogo ou pela Loja do Parceiro.",
    )
else:
    # Cabeçalho da tabela
    h1, h2, h3, h4, h5 = st.columns([4, 1, 1, 2, 1])
    h1.markdown("**Produto**")
    h2.markdown("**Qtd**")
    h3.markdown("**Ajustar**")
    h4.markdown("**Subtotal**")
    h5.markdown("**Remover**")
    components.divider()

    for item in list(cart.values()):
        pid   = item["id"]
        nome  = item["name"]
        preco = item["price"]
        qty   = item["qty"]

        c1, c2, c3, c4, c5 = st.columns([4, 1, 1, 2, 1])
        c1.markdown(f"**{nome}**")
        c2.markdown(f"`x{qty}`")

        # Controles +/-
        with c3:
            col_minus, col_plus = st.columns(2)
            with col_minus:
                if st.button("−", key=f"dec_{pid}", help="Diminuir quantidade"):
                    if qty > 1:
                        st.session_state["cart"][pid]["qty"] -= 1
                    else:
                        del st.session_state["cart"][pid]
                    st.rerun()
            with col_plus:
                if st.button("+", key=f"inc_{pid}", help="Aumentar quantidade"):
                    st.session_state["cart"][pid]["qty"] += 1
                    st.rerun()

        c4.markdown(f"`{ui.brl(preco * qty)}`")

        if c5.button("❌", key=f"rm_{pid}", help="Remover item"):
            ui.remove_from_cart(pid)
            st.rerun()

    components.divider()
    commerce.cart_total_block(ui.cart_total())

    col_l, col_r = st.columns([1, 1])
    with col_l:
        if st.button("🗑️ Limpar carrinho", use_container_width=True):
            ui.clear_cart()
            st.rerun()
    with col_r:
        st.page_link("pages/6_Checkout.py", label="→ Finalizar pedido", icon="💳")
