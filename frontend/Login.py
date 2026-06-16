"""
Login.py — HIPNUS COSMÉTICOS
==============================
Entrypoint real do Streamlit Cloud (configurado no painel como frontend/Login.py).

Navegação:
  Login bem-sucedido  →  pages/0_🏠_Home.py
  Botão Demo         →  pages/0_🏠_Home.py
  require_auth() fail →  Login.py  (página inicial)

Design:
  Usa inject_theme() + inject_login_style() do módulo lib.theme.
  Não carrega CSS inline — toda a estilização vem do design system.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

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
    st.switch_page("pages/0_🏠_Home.py")

# ─ Logo e identidade da marca ────────────────────────────────────────
st.html(f"""
<div class="hip-auth-logo">
    <div class="wordmark">HIPNUS</div>
    <div class="sub">COSMÉTICOS</div>
    <div class="tagline">{BRAND['tagline']}</div>
</div>
""")

# ─ Card de login ─────────────────────────────────────────────────────
st.html('<div class="hip-auth-card">')

st.markdown("#### Entrar na plataforma")

login_input = st.text_input("Usuário", placeholder="seu.usuario", key="_login")
senha_input = st.text_input(
    "Senha", placeholder="••••••••", type="password", key="_senha"
)

col1, col2 = st.columns([2, 1])
with col1:
    btn_entrar = st.button("→ Entrar", use_container_width=True, type="primary")
with col2:
    btn_demo = st.button("Demo", use_container_width=True, help="Acessa a vitrine sem login")

st.html('</div>')

# ─ Feedback de autenticação ──────────────────────────────────────────
if btn_entrar:
    if not login_input or not senha_input:
        st.warning("Preencha usuário e senha para continuar.")
    else:
        ok, msg = fazer_login(login_input.strip(), senha_input)
        if ok:
            st.switch_page("pages/0_🏠_Home.py")
        else:
            st.error(msg)

if btn_demo:
    st.session_state.update({
        "autenticado": True,
        "usuario":     "demo",
        "perfil":      "demo",
        "nome":        "Visitante",
        "display_name": "Modo demonstração",
        "email":       "",
        "token":       None,
        "via_api":     False,
    })
    st.switch_page("pages/0_🏠_Home.py")

# ─ Rodapé ────────────────────────────────────────────────────────────
st.html("""
<div class="hip-auth-footer">
    HIPNUS COSMÉTICOS &copy; 2026 — Plataforma exclusiva da marca.
</div>
""")
