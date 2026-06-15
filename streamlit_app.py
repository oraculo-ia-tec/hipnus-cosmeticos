"""
streamlit_app.py — HIPNUS COSMÉTICOS
======================================
Entrypoint do Streamlit Cloud — página de Login.

As páginas são registradas em pages/ (raiz) como wrappers
que carregam o código real de frontend/pages/.

Navegação:
  Login bem-sucedido  →  st.switch_page("pages/1_Home.py")
  require_auth() fail →  st.switch_page("streamlit_app.py")
  logout()            →  st.switch_page("streamlit_app.py")
"""
import sys
from pathlib import Path

frontend_path = Path(__file__).resolve().parent / "frontend"
if str(frontend_path) not in sys.path:
    sys.path.insert(0, str(frontend_path))

import streamlit as st
from lib.config import COLORS, BRAND
from lib.auth import fazer_login
from lib import ui

st.set_page_config(
    page_title="Login — HIPNUS COSMÉTICOS",
    page_icon="💜",
    layout="centered",
    initial_sidebar_state="collapsed",
)
ui.inject_theme()

st.markdown(
    """
    <style>
    [data-testid="stSidebar"]        { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    #MainMenu { visibility: hidden; }
    header    { visibility: hidden; }
    div[data-testid="stHorizontalBlock"] {
        max-width: 420px !important;
        margin: 0 auto !important;
    }
    div[data-testid="stHorizontalBlock"] button { width: 100%; }
    div[data-testid="stTextInputRootElement"] {
        max-width: 420px !important;
        margin: 0 auto !important;
    }
    .login-title { max-width: 420px; margin: 0 auto 0.5rem auto; }
    </style>
    """,
    unsafe_allow_html=True,
)

if st.session_state.get("autenticado"):
    st.switch_page("pages/1_Home.py")

st.markdown(
    f"""
    <div style="text-align:center; padding:2.5rem 0 1.5rem 0;">
        <div style="font-size:2.8rem; font-weight:800;
                    color:{COLORS['primary']}; letter-spacing:-1px;">HIPNUS</div>
        <div style="font-size:1rem; color:{COLORS['muted']};
                    margin-top:0.2rem; letter-spacing:2px;">COSMÉTICOS</div>
        <div style="margin-top:0.8rem; font-size:0.92rem; color:{COLORS['muted']};">
            {BRAND['tagline']}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    "<div class='login-title'><h4 style='margin-bottom:0.5rem;'>Entrar na plataforma</h4></div>",
    unsafe_allow_html=True,
)

login_input = st.text_input("Usuário", placeholder="seu.usuario", key="_login")
senha_input = st.text_input("Senha", placeholder="\u2022" * 8, type="password", key="_senha")
st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])
with col1:
    btn_entrar = st.button("→ Entrar", use_container_width=True, type="primary")
with col2:
    btn_demo = st.button("Demo", use_container_width=True, help="Acessa a vitrine sem login")

if btn_entrar:
    if not login_input or not senha_input:
        st.warning("⚠️ Preencha usuário e senha.")
    else:
        ok, msg = fazer_login(login_input.strip(), senha_input)
        if ok:
            st.switch_page("pages/1_Home.py")
        else:
            st.error("❌ " + msg)

if btn_demo:
    st.session_state.update({
        "autenticado": True, "usuario": "demo", "perfil": "demo",
        "nome": "Visitante", "display_name": "Modo demonstração",
        "email": "", "token": None, "via_api": False,
    })
    st.switch_page("pages/1_Home.py")

st.markdown(
    f"<div style='text-align:center; margin-top:2rem; font-size:0.78rem; color:{COLORS['muted']};'>"
    "HIPNUS COSMÉTICOS &copy; 2026 — Plataforma exclusiva da marca.</div>",
    unsafe_allow_html=True,
)
