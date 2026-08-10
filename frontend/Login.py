"""
Login.py — TÁLYA COSMÉTICOS
==============================
Este arquivo existe para compatibilidade com navegação interna
(st.switch_page de páginas antigas que ainda apontavam para Login.py).

O entrypoint REAL do Streamlit Cloud é streamlit_app.py (raiz do repo).
Este arquivo delega imediatamente para o entrypoint real.
"""
import streamlit as st

# Redireciona para a página de login dentro de pages/
st.switch_page("pages/Login.py")
