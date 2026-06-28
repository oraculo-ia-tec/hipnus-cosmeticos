"""
5_Checkout.py — HIPNUS COSMÉTICOS
"""
from __future__ import annotations
import sys
from pathlib import Path

_ROOT     = Path(__file__).resolve().parents[2]
_FRONTEND = Path(__file__).resolve().parents[1]
for _p in [str(_ROOT), str(_FRONTEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
from lib import ui, components
from lib.auth import require_auth, build_sidebar
from lib import commerce

st.set_page_config(page_title="Checkout · HIPNUS", page_icon="💳", layout="wide")
ui.inject_theme()
usuario = require_auth()
build_sidebar()

components.page_header(title="Checkout", subtitle="Finalize seu pedido com segurança.")
commerce.checkout_view(usuario)
