"""
Login.py — HIPNUS COSMÉTICOS
==============================
Porta de entrada obrigatória da plataforma.

Fluxo pós-login:
  - Usamos st.rerun() após gravar a sessão.
  - O streamlit_app.py detecta a sessão ativa e encaminha para Home.

Design:
  - Fundo com gradiente animado (mesh gradient suave, tons roxo/violeta).
  - Partículas flutuantes discretas via CSS keyframes.
  - Card de login centralizado com borda translúcida (glassmorphism leve).
  - Título HIPNUS com animação de entrada (fade + slide up).
  - Inputs e botão com hover e foco refinados.
  - Botão Demo REMOVIDO.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

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

# ─── CSS completo: fundo animado + card + animações ────────────────────
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ── Reset e body ── */
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
        margin: 0; padding: 0;
    }}
    #MainMenu, header, footer,
    [data-testid="stSidebar"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarHeader"] {{
        display: none !important;
        visibility: hidden !important;
    }}

    /* ── Fundo animado com gradiente mesh ── */
    .stApp {{
        background: linear-gradient(
            135deg,
            #0f0c1e 0%,
            #1a1230 25%,
            #1e1040 50%,
            #16092e 75%,
            #0b0818 100%
        );
        background-size: 400% 400%;
        animation: gradientShift 18s ease infinite;
        min-height: 100vh;
        position: relative;
        overflow: hidden;
    }}

    @keyframes gradientShift {{
        0%   {{ background-position: 0% 50%;   }}
        50%  {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%;   }}
    }}

    /* ── Orbs de luz suaves no fundo ── */
    .stApp::before {{
        content: '';
        position: fixed;
        top: -20%;
        left: -15%;
        width: 55vw;
        height: 55vw;
        background: radial-gradient(circle, rgba(124,58,237,0.13) 0%, transparent 70%);
        animation: orbFloat1 20s ease-in-out infinite;
        pointer-events: none;
        z-index: 0;
    }}
    .stApp::after {{
        content: '';
        position: fixed;
        bottom: -20%;
        right: -10%;
        width: 50vw;
        height: 50vw;
        background: radial-gradient(circle, rgba(167,139,250,0.10) 0%, transparent 70%);
        animation: orbFloat2 25s ease-in-out infinite;
        pointer-events: none;
        z-index: 0;
    }}
    @keyframes orbFloat1 {{
        0%, 100% {{ transform: translate(0, 0) scale(1);    }}
        33%       {{ transform: translate(4vw, 3vh) scale(1.05); }}
        66%       {{ transform: translate(-2vw, 5vh) scale(0.97); }}
    }}
    @keyframes orbFloat2 {{
        0%, 100% {{ transform: translate(0, 0) scale(1);    }}
        33%       {{ transform: translate(-3vw, -4vh) scale(1.04); }}
        66%       {{ transform: translate(2vw, -2vh) scale(0.98); }}
    }}

    /* ── Container principal centralizado ── */
    .block-container {{
        max-width: 460px !important;
        padding: 0 1.5rem !important;
        margin: 0 auto !important;
        position: relative;
        z-index: 10;
    }}

    /* ── Card glassmorphism ── */
    .hip-login-card {{
        background: rgba(255, 255, 255, 0.045);
        backdrop-filter: blur(24px) saturate(1.4);
        -webkit-backdrop-filter: blur(24px) saturate(1.4);
        border: 1px solid rgba(167, 139, 250, 0.22);
        border-radius: 24px;
        padding: 3rem 2.5rem 2.5rem;
        box-shadow:
            0 4px 24px rgba(0, 0, 0, 0.45),
            0 1px 0 rgba(255,255,255,0.06) inset,
            0 0 0 1px rgba(124,58,237,0.08) inset;
        animation: cardEntrance 0.7s cubic-bezier(0.16, 1, 0.3, 1) both;
    }}
    @keyframes cardEntrance {{
        from {{ opacity: 0; transform: translateY(28px) scale(0.97); }}
        to   {{ opacity: 1; transform: translateY(0)    scale(1);    }}
    }}

    /* ── Logo H ── */
    .hip-logo-badge {{
        width: 64px; height: 64px;
        background: linear-gradient(135deg, {COLORS['primary']}, {COLORS.get('accent', '#a78bfa')});
        border-radius: 18px;
        display: flex; align-items: center; justify-content: center;
        font-weight: 900; font-size: 1.9rem; color: #fff;
        margin: 0 auto 1.2rem auto;
        box-shadow: 0 8px 24px -8px rgba(124,58,237,0.7);
        animation: logoPulse 3s ease-in-out infinite;
    }}
    @keyframes logoPulse {{
        0%, 100% {{ box-shadow: 0 8px 24px -8px rgba(124,58,237,0.7); }}
        50%       {{ box-shadow: 0 8px 32px -4px rgba(124,58,237,0.95); }}
    }}

    /* ── Título animado ── */
    .hip-login-brand {{
        text-align: center;
        animation: fadeSlideUp 0.8s cubic-bezier(0.16,1,0.3,1) 0.15s both;
    }}
    .hip-login-brand .brand-name {{
        font-size: 2rem;
        font-weight: 800;
        color: #f5f3ff;
        letter-spacing: -1px;
        line-height: 1;
    }}
    .hip-login-brand .brand-sub {{
        font-size: 0.72rem;
        font-weight: 600;
        color: rgba(167,139,250,0.8);
        letter-spacing: 3.5px;
        text-transform: uppercase;
        margin-top: 4px;
    }}
    .hip-login-brand .brand-tagline {{
        font-size: 0.83rem;
        color: rgba(255,255,255,0.42);
        margin-top: 0.55rem;
        font-weight: 400;
    }}

    @keyframes fadeSlideUp {{
        from {{ opacity: 0; transform: translateY(16px); }}
        to   {{ opacity: 1; transform: translateY(0);    }}
    }}

    /* ── Divisor ── */
    .hip-divider {{
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(167,139,250,0.25), transparent);
        margin: 1.6rem 0 1.4rem;
        animation: fadeIn 1s 0.4s both;
    }}

    /* ── Label dos inputs ── */
    .hip-label {{
        font-size: 0.78rem;
        font-weight: 600;
        color: rgba(200,190,255,0.75);
        letter-spacing: 0.5px;
        margin-bottom: 4px;
        display: block;
        animation: fadeIn 0.8s 0.5s both;
    }}

    @keyframes fadeIn {{
        from {{ opacity: 0; }}
        to   {{ opacity: 1; }}
    }}

    /* ── Inputs Streamlit estilizados ── */
    div[data-testid="stTextInputRootElement"] {{
        animation: fadeSlideUp 0.8s cubic-bezier(0.16,1,0.3,1) 0.5s both;
    }}
    div[data-testid="stTextInputRootElement"] input {{
        background: rgba(255,255,255,0.055) !important;
        border: 1px solid rgba(167,139,250,0.28) !important;
        border-radius: 12px !important;
        color: #f0ecff !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.95rem !important;
        padding: 0.65rem 1rem !important;
        transition: border-color 0.22s ease, box-shadow 0.22s ease, background 0.22s ease !important;
    }}
    div[data-testid="stTextInputRootElement"] input:focus {{
        background: rgba(255,255,255,0.08) !important;
        border-color: rgba(167,139,250,0.7) !important;
        box-shadow: 0 0 0 3px rgba(124,58,237,0.2) !important;
        outline: none !important;
    }}
    div[data-testid="stTextInputRootElement"] input::placeholder {{
        color: rgba(255,255,255,0.22) !important;
    }}
    div[data-testid="stTextInputRootElement"] label {{
        color: rgba(200,190,255,0.75) !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.4px !important;
    }}

    /* ── Botão Entrar ── */
    div.stButton > button {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS.get('accent', '#7c3aed')} 100%) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 12px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.3px !important;
        padding: 0.65rem 1.5rem !important;
        width: 100% !important;
        cursor: pointer !important;
        transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease !important;
        box-shadow: 0 6px 20px -6px rgba(124,58,237,0.65) !important;
        animation: fadeSlideUp 0.8s cubic-bezier(0.16,1,0.3,1) 0.7s both;
    }}
    div.stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 28px -6px rgba(124,58,237,0.8) !important;
        filter: brightness(1.1) !important;
    }}
    div.stButton > button:active {{
        transform: translateY(0px) !important;
        filter: brightness(0.95) !important;
    }}

    /* ── Rodapé ── */
    .hip-footer {{
        text-align: center;
        margin-top: 1.8rem;
        font-size: 0.72rem;
        color: rgba(255,255,255,0.22);
        animation: fadeIn 1s 1s both;
        letter-spacing: 0.3px;
    }}

    /* ── Alertas Streamlit ── */
    div[data-testid="stAlert"] {{
        border-radius: 10px !important;
        font-size: 0.85rem !important;
        animation: fadeSlideUp 0.4s ease both;
    }}

    /* ── Remove borda padrão dos inputs no modo dark ── */
    [data-baseweb="input"] {{ border-radius: 12px !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Se já autenticado, redireciona para Home
if st.session_state.get("autenticado"):
    st.switch_page("frontend/pages/0_🏠_Home.py")

# ─── Card de login ───────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="hip-login-card">
      <div class="hip-logo-badge">H</div>
      <div class="hip-login-brand">
        <div class="brand-name">HIPNUS</div>
        <div class="brand-sub">Cosméticos</div>
        <div class="brand-tagline">{BRAND['tagline']}</div>
      </div>
      <div class="hip-divider"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─── Campos dentro do card (Streamlit nativo) ────────────────────────
with st.container():
    login_input = st.text_input("Usuário", placeholder="seu.usuario", key="_login")
    senha_input = st.text_input(
        "Senha", placeholder="••••••••", type="password", key="_senha"
    )

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    btn_entrar = st.button("→ Entrar na plataforma", use_container_width=True, type="primary")

# ─── Lógica de login ─────────────────────────────────────────────────
if btn_entrar:
    if not login_input or not senha_input:
        st.warning("⚠️ Preencha usuário e senha.")
    else:
        ok, msg = fazer_login(login_input.strip(), senha_input)
        if ok:
            st.success(msg)
            st.switch_page("frontend/pages/0_🏠_Home.py")
        else:
            st.error("❌ " + msg)

# ─── Rodapé ──────────────────────────────────────────────────────────
st.markdown(
    "<div class='hip-footer'>"
    "HIPNUS COSMÉTICOS &copy; 2026 &nbsp;·&nbsp; Plataforma exclusiva da marca."
    "</div>",
    unsafe_allow_html=True,
)
