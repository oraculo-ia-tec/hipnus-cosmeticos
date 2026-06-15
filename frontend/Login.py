"""
Login.py — HIPNUS COSMÉTICOS
==============================
Porta de entrada obrigatória da plataforma.

Fluxo:
  1. Usuário não autenticado → exibe formulário de login.
  2. Credenciais válidas → grava st.session_state e redireciona para Home.
  3. Todas as outras páginas verificam st.session_state[’autenticado’].

Modos de usuário:
  - admin   : acesso total (gerenciamento, relatórios, configurações)
  - b2b     : profissional / salão / distribuidor
  - b2c     : consumidor final
  - demo    : vitrine pública sem login (somente catálogo)

Senhas de desenvolvimento (substituír por autenticação real via API):
  admin / hipnus@2026
  pro   / hipnus@pro
  user  / hipnus@user
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from lib.config import COLORS, BRAND
from lib import ui

st.set_page_config(
    page_title="Login — HIPNUS COSMÉTICOS",
    page_icon="💜",
    layout="centered",
    initial_sidebar_state="collapsed",
)
ui.inject_theme()

# ─── Oculta sidebar e navegação na página de login ─────────────────────
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    #MainMenu { visibility: hidden; }
    header { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Se já autenticado, redireciona para Home ──────────────────────────
if st.session_state.get("autenticado"):
    st.switch_page("pages/0_🏠_Home.py")

# ─── Usuários válidos (dev) — substituir por chamada à API em produção ───
USUARIOS = {
    "admin": {"senha": "hipnus@2026", "perfil": "admin",  "nome": "Administrador"},
    "pro":   {"senha": "hipnus@pro",  "perfil": "b2b",    "nome": "Profissional"},
    "user":  {"senha": "hipnus@user", "perfil": "b2c",    "nome": "Cliente"},
}

# ─── Layout da página de login ──────────────────────────────────────
st.markdown(
    f"""
    <div style="text-align:center; padding: 2.5rem 0 1.5rem 0;">
        <div style="font-size:2.8rem; font-weight:800; color:{COLORS['primary']}; letter-spacing:-1px;">
            HIPNUS
        </div>
        <div style="font-size:1rem; color:{COLORS['muted']}; margin-top:0.2rem; letter-spacing:2px;">
            COSMÉTICOS
        </div>
        <div style="margin-top:0.8rem; font-size:0.92rem; color:{COLORS['muted']};">
            {BRAND['tagline']}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.container():
    st.markdown(
        f'<div style="background:{COLORS["surface"]}; border:1px solid {COLORS["border"]};'
        'border-radius:12px; padding:2rem 2.5rem; max-width:420px; margin:0 auto;">',
        unsafe_allow_html=True,
    )

    st.markdown("#### Entrar na plataforma")
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    login = st.text_input("Usuário", placeholder="seu.usuario", key="login_user")
    senha = st.text_input("Senha",   placeholder="\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022",
                          type="password", key="login_pass")

    col1, col2 = st.columns([2, 1])
    with col1:
        entrar = st.button("Entrar", use_container_width=True, type="primary")
    with col2:
        demo = st.button("Demo", use_container_width=True, help="Acessa a vitrine sem login")

    st.markdown("</div>", unsafe_allow_html=True)

# ─── Lógica de autenticação ──────────────────────────────────────────
if entrar:
    usuario = USUARIOS.get(login.strip().lower())
    if usuario and senha == usuario["senha"]:
        st.session_state["autenticado"] = True
        st.session_state["usuario"]     = login.strip().lower()
        st.session_state["perfil"]      = usuario["perfil"]
        st.session_state["nome"]        = usuario["nome"]
        st.success(f"Bem-vindo(a), {usuario['nome']}!")
        st.switch_page("pages/0_🏠_Home.py")
    else:
        st.error("❌ Usuário ou senha incorretos.")

if demo:
    st.session_state["autenticado"] = True
    st.session_state["usuario"]     = "demo"
    st.session_state["perfil"]      = "demo"
    st.session_state["nome"]        = "Visitante"
    st.switch_page("pages/0_🏠_Home.py")

# ─── Rodapé ──────────────────────────────────────────────────────────────
st.markdown(
    f"<div style='text-align:center; margin-top:2rem; font-size:0.78rem; color:{COLORS['muted']};'>"
    "HIPNUS COSMÉTICOS &copy; 2026 — Plataforma exclusiva da marca."
    "</div>",
    unsafe_allow_html=True,
)
