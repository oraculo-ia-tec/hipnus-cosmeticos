"""
streamlit_app.py — HIPNUS COSMÉTICOS
======================================
Entrypoint para o Streamlit Cloud.

Esta página é a raiz do app. Ela é registrada como a página inicial
pelo Streamlit Cloud e simplesmente redireciona para Login.py,
que está dentro de frontend/.

Solução de compatibilidade:
  - Não usamos exec() pois ele quebra o contexto de navegação do Streamlit.
  - O Streamlit Cloud registra automaticamente todos os arquivos .py dentro
    de pages/ (e também frontend/pages/) como páginas navegaveis.
  - Usamos st.switch_page apontando para o Login dentro de frontend/.
"""
import sys
from pathlib import Path

frontend_path = Path(__file__).resolve().parent / "frontend"
if str(frontend_path) not in sys.path:
    sys.path.insert(0, str(frontend_path))

import streamlit as st

st.switch_page("frontend/Login.py")
