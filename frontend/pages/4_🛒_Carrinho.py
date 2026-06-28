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

# Garante que session_state["cart"] existe como dict (chave única do sistema)
if "cart" not in st.session_state or not isinstance(st.session_state["cart"], dict):
    st.session_state["cart"] = {}

build_sidebar(show_cart=True, cart_count=ui.cart_count())

components.page_header(
    title="Carrinho",
    subtitle="Revise os itens antes de finalizar o pedido.",
)

# cart_view() já lê internamente session_state["cart"] via _cart()
commerce.cart_view()
