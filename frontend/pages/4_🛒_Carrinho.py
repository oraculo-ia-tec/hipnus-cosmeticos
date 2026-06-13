"""
Página de Carrinho — itens selecionados pelo cliente.

Permite revisar itens, ajustar quantidades, remover e ver o total.
O checkout com pagamento (split Asaas) será habilitado no próximo ciclo —
o botão fica visível e desativado, sinalizando o roadmap.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st  # noqa: E402

from lib import api, ui  # noqa: E402

st.set_page_config(page_title="Carrinho · HIPNUS", page_icon="🛒", layout="wide")
ui.inject_theme()

ui.brand_header()
ui.api_status_badge(api.api_online())

st.markdown('<div class="hip-section-title">Seu carrinho</div>', unsafe_allow_html=True)

cart = st.session_state.get("cart", {})

if not cart:
    st.info("Seu carrinho está vazio. Visite o catálogo para adicionar produtos.")
    st.page_link("pages/1_🛍️_Catálogo.py", label="Ir para o catálogo", icon="🛍️")
else:
    # Cabeçalho da tabela
    h = st.columns([4, 1.4, 1.4, 1.6, 1])
    for col, label in zip(h, ["Produto", "Preço", "Qtd", "Subtotal", ""]):
        col.markdown(f"**{label}**")

    for item in list(cart.values()):
        c = st.columns([4, 1.4, 1.4, 1.6, 1])
        c[0].write(item["name"])
        c[1].write(ui.brl(item["price"]))
        new_qty = c[2].number_input(
            "qtd", min_value=1, max_value=99, value=item["qty"],
            key=f"qty_{item['id']}", label_visibility="collapsed",
        )
        if new_qty != item["qty"]:
            cart[item["id"]]["qty"] = new_qty
            st.rerun()
        c[3].write(ui.brl(item["price"] * item["qty"]))
        if c[4].button("🗑️", key=f"rm_{item['id']}"):
            ui.remove_from_cart(item["id"])
            st.rerun()

    st.markdown("---")
    left, right = st.columns([3, 1.4])
    with right:
        st.markdown(f"### Total: {ui.brl(ui.cart_total())}")
        st.button("Finalizar compra", type="primary", use_container_width=True, disabled=True,
                  help="Checkout com pagamento (split Asaas) será habilitado no próximo ciclo.")
        if st.button("Limpar carrinho", use_container_width=True):
            ui.clear_cart()
            st.rerun()
    with left:
        st.caption("O pagamento online com split automático via Asaas será habilitado no "
                   "próximo ciclo de desenvolvimento (módulo de pedidos/checkout). "
                   "Cada item será dividido entre a Hipnus (piso) e o parceiro (margem).")
