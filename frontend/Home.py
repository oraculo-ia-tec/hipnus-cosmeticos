"""
Home.py — HIPNUS COSMÉTICOS
==============================
Este arquivo existe para compatibilidade com navegação interna.

O entrypoint REAL do Streamlit Cloud é streamlit_app.py (raiz).
Após login bem-sucedido, o usuário é redirecionado para
pages/0_🏠_Home.py (página Home real no menu do Streamlit).
"""
import streamlit as st

# Redireciona para a página Home real do menu
st.switch_page("pages/0_\U0001f3e0_Home.py")
