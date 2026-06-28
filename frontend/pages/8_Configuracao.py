"""
8_Configuracao.py — HIPNUS COSMÉTICOS
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

st.set_page_config(page_title="Configurações · HIPNUS", page_icon="⚙️", layout="wide")
ui.inject_theme()
usuario = require_auth(perfis_permitidos=["super_admin", "admin"])
build_sidebar()

components.page_header(
    title="Configurações",
    subtitle="Gerencie parâmetros e integrações da plataforma.",
    kicker="⚙️ Painel de Configuração",
)

st.info("🛠️ Página de configurações em desenvolvimento.")
