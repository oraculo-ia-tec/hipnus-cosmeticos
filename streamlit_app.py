"""
streamlit_app.py — HIPNUS COSMÉTICOS
======================================
Entrypoint do Streamlit Cloud — esta é a página de Login.

No Streamlit Cloud, o arquivo raiz (streamlit_app.py) é a primeira página
exibida. Não é possível usar st.switch_page() nele antes de renderizar.
A solução correta é: este arquivo É o Login.

As páginas internas ficam em frontend/pages/ e são registradas
automaticamente pelo Streamlit Cloud como páginas do menu.

Fluxo de navegação:
  streamlit_app.py  (Login)
        ↓ login bem-sucedido
  frontend/pages/0_Home.py
        ↓ require_auth() falha
  st.switch_page("streamlit_app.py")  ← volta para o Login
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

# ─── Oculta sidebar/menu e controla largura dos botões ──────────────
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

# Se já autenticado, vai direto para Home
if st.session_state.get("autenticado"):
    st.switch_page("frontend/pages/0_🏠_Home.py")

# ─── Cabeçalho da marca ─────────────────────────────────────────────
st.markdown(
    f"""
    <div style="text-align:center; padding:2.5rem 0 1.5rem 0;">
        <div style="font-size:2.8rem; font-weight:800;
                    color:{COLORS['primary']}; letter-spacing:-1px;">
            HIPNUS
        </div>
        <div style="font-size:1rem; color:{COLORS['muted']};
                    margin-top:0.2rem; letter-spacing:2px;">
            COSMÉTICOS
        </div>
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
senha_input = st.text_input("Senha",   placeholder="\u2022" * 8,
                             type="password", key="_senha")

st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])
with col1:
    btn_entrar = st.button("→ Entrar", use_container_width=True, type="primary")
with col2:
    btn_demo = st.button("Demo", use_container_width=True,
                         help="Acessa a vitrine sem login")

if btn_entrar:
    if not login_input or not senha_input:
        st.warning("⚠️ Preencha usuário e senha.")
    else:
        ok, msg = fazer_login(login_input.strip(), senha_input)
        if ok:
            st.switch_page("frontend/pages/0_🏠_Home.py")
        else:
            st.error("❌ " + msg)

if btn_demo:
    st.session_state["autenticado"]  = True
    st.session_state["usuario"]      = "demo"
    st.session_state["perfil"]       = "demo"
    st.session_state["nome"]         = "Visitante"
    st.session_state["display_name"] = "Modo demonstração"
    st.session_state["email"]        = ""
    st.session_state["token"]        = None
    st.session_state["via_api"]      = False
    st.switch_page("frontend/pages/0_🏠_Home.py")

st.markdown(
    f"<div style='text-align:center; margin-top:2rem; font-size:0.78rem; color:{COLORS['muted']};'>"
    "HIPNUS COSMÉTICOS &copy; 2026 — Plataforma exclusiva da marca."
    "</div>",
    unsafe_allow_html=True,
)
