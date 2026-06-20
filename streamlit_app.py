"""
streamlit_app.py — HIPNUS COSMÉTICOS
======================================
Entrypoint do Streamlit Cloud — página de Login.

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
from lib.config import BRAND
from lib.auth import fazer_login
from lib.theme import inject_theme, inject_login_style

# ─ Configuração da página ────────────────────────────────────────────
st.set_page_config(
    page_title="Login — HIPNUS COSMÉTICOS",
    page_icon="💜",
    layout="centered",
    initial_sidebar_state="collapsed",
)
inject_theme()
inject_login_style()

# ─ Redireciona se já autenticado ─────────────────────────────────────
if st.session_state.get("autenticado"):
    st.switch_page("pages/1_Home.py")

# ─ Logo e identidade da marca ────────────────────────────────────────
st.html(f"""
<div class="hip-auth-logo">
    <div class="logo-icon">H</div>
    <div class="wordmark">HIPNUS</div>
    <div class="sub">COSMÉTICOS</div>
    <div class="tagline">{BRAND['tagline']}</div>
    <div class="divider-dot"></div>
</div>
""")

# ─ Card de login ─────────────────────────────────────────────────────
st.html('<div class="hip-auth-card">')

st.html('<div class="hip-auth-card-title">Entrar na plataforma</div>')

login_input = st.text_input(
    "Usuário",
    placeholder="seu.usuario",
    key="_login",
    label_visibility="visible",
)
senha_input = st.text_input(
    "Senha",
    placeholder="••••••••",
    type="password",
    key="_senha",
    label_visibility="visible",
)

col1, col2 = st.columns([3, 1])
with col1:
    btn_entrar = st.button(
        "Entrar  →",
        use_container_width=True,
        type="primary",
        key="btn_entrar",
    )
with col2:
    btn_demo = st.button(
        "Demo",
        use_container_width=True,
        help="Acessa a vitrine em modo demonstração, sem criar conta.",
        key="btn_demo",
    )

st.html('</div>')

# ─ Feedback de autenticação ──────────────────────────────────────────
if btn_entrar:
    if not login_input or not senha_input:
        st.warning("Preencha usuário e senha para continuar.")
    else:
        ok, msg = fazer_login(login_input.strip(), senha_input)
        if ok:
            st.switch_page("pages/1_Home.py")
        else:
            st.error(msg)

if btn_demo:
    st.session_state.update({
        "autenticado": True, "usuario": "demo", "perfil": "demo",
        "nome": "Visitante", "display_name": "Modo demonstração",
        "email": "", "token": None, "via_api": False,
    })
    st.switch_page("pages/1_Home.py")

# ─ Rodapé ────────────────────────────────────────────────────────────
st.html("""
<div class="hip-auth-footer">
    HIPNUS COSMÉTICOS &copy; 2026 &mdash; Plataforma exclusiva da marca.<br>
    Acesso restrito a usuários autorizados.
</div>
""")
