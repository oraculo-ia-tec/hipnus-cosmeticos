"""
4_Carrinho.py — HIPNUS COSMÉTICOS
===================================
Página de Carrinho — itens selecionados pelo cliente.

Permite revisar itens, ajustar quantidades, remover e ver o total.
O botão de checkout redireciona para a página de pagamento.

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

st.set_page_config(page_title="Carrinho · HIPNUS", page_icon="🛒", layout="wide")
ui.inject_theme()

require_auth()

# ─── Sidebar ───────────────────────────────────────────────────────────
ui.brand_header()                       # 1. Logo
sidebar_user_info()                     # 2. Usuário (ACIMA do menu)
# --- [menu nativo Streamlit aqui] ---
ui.api_status_badge(api.api_online())   # 4. Status API
ui.sidebar_cart_summary()               # 5. Carrinho
sidebar_logout_button()                 # 6. SAIR (ABAIXO do menu)

st.markdown('<div class="hip-section-title">Seu carrinho</div>', unsafe_allow_html=True)

cart = st.session_state.get("cart", {})

if not cart:
    st.info("Seu carrinho está vazio. Visite o catálogo para adicionar produtos.")
    st.page_link("pages/2_Catalogo.py", label="Ir para o catálogo", icon="🛍️")
else:
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
        if st.button("Finalizar compra 💳", type="primary", use_container_width=True):
            st.switch_page("pages/5_💳_Checkout.py")
        if st.button("Limpar carrinho", use_container_width=True):
            ui.clear_cart()
            st.rerun()
    with left:
        st.caption(
            "O pagamento é processado via **Asaas** com split automático: "
            "o piso (floor_price) fica na Hipnus e a margem é repassada ao parceiro."
        )
