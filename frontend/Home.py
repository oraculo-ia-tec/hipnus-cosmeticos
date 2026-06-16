"""
Home.py — HIPNUS COSMÉTICOS
================================
Entry point do Streamlit Cloud.

Se o usuário não estiver autenticado, redireciona para Login.py.
Se já estiver autenticado, redireciona para a página principal.

Executar: streamlit run frontend/Home.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

st.set_page_config(
    page_title="HIPNUS COSMÉTICOS",
    page_icon="💜",
    layout="centered",
    initial_sidebar_state="collapsed",
)

if st.session_state.get("autenticado"):
    st.switch_page("pages/0_🏠_Home.py")
else:
    st.switch_page("Login.py")
