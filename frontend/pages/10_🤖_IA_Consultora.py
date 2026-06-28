"""
10_IA_Consultora.py — HIPNUS COSMÉTICOS
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

st.set_page_config(page_title="IA Consultora · HIPNUS", page_icon="🤖", layout="wide")
ui.inject_theme()
usuario = require_auth()
build_sidebar()

components.page_header(
    title="IA Consultora",
    subtitle="Tire dúvidas sobre produtos, linhas e cuidados capilares com nossa IA especializada.",
    kicker="🤖 Assistente Hipnus",
)

if "ia_msgs" not in st.session_state:
    st.session_state["ia_msgs"] = [
        {"role": "assistant", "content": "Olá! Sou a consultora virtual da Hipnus Cosméticos. Como posso te ajudar hoje? 💜"}
    ]

for msg in st.session_state["ia_msgs"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Pergunte sobre produtos, linhas ou cuidados..."):
    st.session_state["ia_msgs"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            from lib.ia_client import consultar_ia
            resposta = consultar_ia(prompt, historico=st.session_state["ia_msgs"][:-1])
        except Exception:
            resposta = (
                "No momento estou sem conexão com o servidor de IA. "
                "Por favor, tente novamente em instantes ou entre em contato com nosso suporte. 💜"
            )
        st.markdown(resposta)
        st.session_state["ia_msgs"].append({"role": "assistant", "content": resposta})
