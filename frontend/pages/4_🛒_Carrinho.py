"""
4_Carrinho.py — HIPNUS COSMÉTICOS
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from lib import ui
from lib.auth import require_auth, build_sidebar
from lib import components, commerce

st.set_page_config(page_title="Carrinho · HIPNUS", page_icon="🛒", layout="wide")
ui.inject_theme()
require_auth()

cart = st.session_state.get("carrinho", [])
build_sidebar(show_cart=True, cart_count=len(cart))

components.page_header(title="Carrinho", subtitle="Revise os itens antes de finalizar o pedido.")

if not cart:
    components.empty_state(icon="🛒", title="Carrinho vazio", message="Adicione produtos pelo Catálogo ou Loja do Parceiro.")
else:
    commerce.cart_view(cart, on_remove=ui.remove_from_cart, on_clear=ui.clear_cart)
