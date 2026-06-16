"""
Login.py — HIPNUS COSMÉTICOS
==============================
Entrypoint real do Streamlit Cloud.
Layout nativo Streamlit — sem CSS inline.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from lib.config import BRAND
from lib.auth import fazer_login

st.set_page_config(
    page_title="Login — HIPNUS COSMÉTICOS",
    page_icon="💜",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─ Esconde sidebar e chrome do Streamlit ───────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
#MainMenu, header, footer,
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
[data-testid="stToolbar"] { display: none !important; }
.block-container { max-width: 420px !important; padding-top: 3rem !important; }

/* Logo */
.hip-logo-wrap { text-align: center; margin-bottom: 2rem; }
.hip-wordmark {
    font-size: 2.8rem; font-weight: 800; letter-spacing: -2px;
    color: #7c3aed; line-height: 1;
}
.hip-cosmeticos {
    font-size: .7rem; letter-spacing: 4px; font-weight: 600;
    color: #6b7280; text-transform: uppercase; margin-top: 4px;
}
.hip-tagline {
    font-size: .82rem; color: #9ca3af; margin-top: 8px;
}

/* Card */
.hip-login-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 32px 32px 28px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.06);
    margin-bottom: 1rem;
}
.hip-login-title {
    font-size: 1.1rem; font-weight: 700;
    color: #111827; margin-bottom: 1.4rem;
}

/* Inputs */
div[data-testid="stTextInputRootElement"] input {
    border-radius: 10px !important;
    border: 1px solid #d1d5db !important;
    font-size: .95rem !important;
    padding: 0.6rem 0.9rem !important;
    transition: border-color .2s !important;
}
div[data-testid="stTextInputRootElement"] input:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,.12) !important;
    outline: none !important;
}

/* Botão primário */
div.stButton > button[kind="primary"] {
    background: #7c3aed !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: .95rem !important;
    color: #fff !important;
    padding: .6rem 1rem !important;
    width: 100% !important;
    transition: background .18s !important;
}
div.stButton > button[kind="primary"]:hover {
    background: #6d28d9 !important;
}

/* Botão Demo */
div.stButton > button:not([kind="primary"]) {
    border-radius: 10px !important;
    border: 1px solid #d1d5db !important;
    font-weight: 600 !important;
    color: #374151 !important;
    width: 100% !important;
}

/* Footer */
.hip-login-footer {
    text-align: center; margin-top: 1.5rem;
    font-size: .7rem; color: #9ca3af;
}
</style>
""", unsafe_allow_html=True)

# ─ Redireciona se já autenticado ─────────────────────────────────
if st.session_state.get("autenticado"):
    st.switch_page("pages/0_🏠_Home.py")

# ─ Logo ──────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hip-logo-wrap">
    <div class="hip-wordmark">HIPNUS</div>
    <div class="hip-cosmeticos">Cosméticos</div>
    <div class="hip-tagline">{BRAND['tagline']}</div>
</div>
""", unsafe_allow_html=True)

# ─ Card + form ──────────────────────────────────────────────────
st.markdown('<div class="hip-login-card"><div class="hip-login-title">🔐 Entrar na plataforma</div>', unsafe_allow_html=True)

login_input = st.text_input("Usuário", placeholder="seu.usuario", key="_login", label_visibility="visible")
senha_input = st.text_input("Senha", placeholder="••••••••", type="password", key="_senha", label_visibility="visible")

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col1:
    btn_entrar = st.button("→ Entrar", use_container_width=True, type="primary", key="btn_entrar")
with col2:
    btn_demo = st.button("Demo", use_container_width=True, key="btn_demo")

st.markdown('</div>', unsafe_allow_html=True)

# ─ Lógica ─────────────────────────────────────────────────────────────
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
        "autenticado":  True,
        "usuario":      "demo",
        "perfil":       "demo",
        "nome":         "Visitante",
        "display_name": "Modo demonstração",
        "email":        "",
        "token":        None,
        "via_api":      False,
    })
    st.switch_page("pages/0_🏠_Home.py")

# ─ Rodapé ────────────────────────────────────────────────────────────
st.markdown(
    "<div class='hip-login-footer'>HIPNUS COSMÉTICOS &copy; 2026 — Plataforma exclusiva da marca.</div>",
    unsafe_allow_html=True,
)
