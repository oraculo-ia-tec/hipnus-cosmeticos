"""
Login.py — HIPNUS COSMÉTICOS
==============================
Tela de login com design premium:
  - Fundo escuro com gradiente animado
  - Orbs de luz flutuantes discretas
  - Card glassmorphism com borda translucida
  - Animacoes fadeSlideUp nas fontes
  - Logo H com brilho pulsante
  - Botao Demo REMOVIDO
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
import streamlit.components.v1 as components
from lib.config import COLORS, BRAND
from lib.auth import fazer_login

st.set_page_config(
    page_title="Login — HIPNUS COSMÉTICOS",
    page_icon="💜",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Redireciona se já autenticado
if st.session_state.get("autenticado"):
    st.switch_page("pages/0_🏠_Home.py")

# ─── CSS global injetado via markdown ────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    margin: 0; padding: 0;
}

/* Oculta elementos padrão */
#MainMenu, header, footer,
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
[data-testid="stSidebarHeader"],
[data-testid="stToolbar"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
}

/* Fundo animado */
.stApp {
    background: linear-gradient(135deg, #0f0c1e 0%, #1a1230 25%, #1e1040 50%, #16092e 75%, #0b0818 100%) !important;
    background-size: 400% 400% !important;
    animation: gradientShift 18s ease infinite !important;
    min-height: 100vh;
}

@keyframes gradientShift {
    0%   { background-position: 0% 50%;   }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%;   }
}

/* Orb de luz superior esquerdo */
.stApp::before {
    content: '';
    position: fixed;
    top: -20%; left: -15%;
    width: 55vw; height: 55vw;
    background: radial-gradient(circle, rgba(124,58,237,0.14) 0%, transparent 70%);
    animation: orbFloat1 20s ease-in-out infinite;
    pointer-events: none;
    z-index: 0;
}
/* Orb inferior direito */
.stApp::after {
    content: '';
    position: fixed;
    bottom: -20%; right: -10%;
    width: 50vw; height: 50vw;
    background: radial-gradient(circle, rgba(167,139,250,0.10) 0%, transparent 70%);
    animation: orbFloat2 25s ease-in-out infinite;
    pointer-events: none;
    z-index: 0;
}
@keyframes orbFloat1 {
    0%, 100% { transform: translate(0,0) scale(1); }
    33%       { transform: translate(4vw,3vh) scale(1.05); }
    66%       { transform: translate(-2vw,5vh) scale(0.97); }
}
@keyframes orbFloat2 {
    0%, 100% { transform: translate(0,0) scale(1); }
    33%       { transform: translate(-3vw,-4vh) scale(1.04); }
    66%       { transform: translate(2vw,-2vh) scale(0.98); }
}

/* Container centralizado */
.block-container {
    max-width: 460px !important;
    padding: 4rem 1.5rem 2rem !important;
    margin: 0 auto !important;
    position: relative;
    z-index: 10;
}

/* Card glassmorphism */
.hip-card {
    background: rgba(255,255,255,0.045) !important;
    backdrop-filter: blur(24px) saturate(1.4) !important;
    -webkit-backdrop-filter: blur(24px) saturate(1.4) !important;
    border: 1px solid rgba(167,139,250,0.25) !important;
    border-radius: 24px !important;
    padding: 2.8rem 2.5rem 2.2rem !important;
    box-shadow: 0 4px 32px rgba(0,0,0,0.5), 0 1px 0 rgba(255,255,255,0.06) inset !important;
    animation: cardEntrance 0.7s cubic-bezier(0.16,1,0.3,1) both !important;
}
@keyframes cardEntrance {
    from { opacity: 0; transform: translateY(28px) scale(0.97); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
}

/* Logo badge H */
.hip-logo {
    width: 64px; height: 64px;
    background: linear-gradient(135deg, #7c3aed, #a78bfa);
    border-radius: 18px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 2rem; color: #fff;
    margin: 0 auto 1.2rem auto;
    box-shadow: 0 8px 28px -8px rgba(124,58,237,0.8);
    animation: logoPulse 3s ease-in-out infinite;
}
@keyframes logoPulse {
    0%,100% { box-shadow: 0 8px 24px -8px rgba(124,58,237,0.7); }
    50%      { box-shadow: 0 8px 36px -4px rgba(124,58,237,1.0); }
}

/* Brand name */
.hip-brand-name {
    text-align: center;
    animation: fadeSlideUp 0.8s cubic-bezier(0.16,1,0.3,1) 0.15s both;
}
.hip-brand-name .name {
    font-size: 2rem; font-weight: 800;
    color: #f5f3ff; letter-spacing: -1px; line-height:1;
}
.hip-brand-name .sub {
    font-size: 0.7rem; font-weight: 600;
    color: rgba(167,139,250,0.85);
    letter-spacing: 4px; text-transform: uppercase; margin-top: 4px;
}
.hip-brand-name .tagline {
    font-size: 0.82rem;
    color: rgba(255,255,255,0.4);
    margin-top: 0.5rem;
}

@keyframes fadeSlideUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
}

/* Divisor */
.hip-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(167,139,250,0.3), transparent);
    margin: 1.5rem 0 1.4rem;
    animation: fadeIn 1s 0.4s both;
}

/* Inputs */
div[data-testid="stTextInputRootElement"] {
    animation: fadeSlideUp 0.8s cubic-bezier(0.16,1,0.3,1) 0.45s both;
}
div[data-testid="stTextInputRootElement"] input {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(167,139,250,0.3) !important;
    border-radius: 12px !important;
    color: #f0ecff !important;
    font-size: 0.95rem !important;
    padding: 0.65rem 1rem !important;
    transition: border-color 0.22s ease, box-shadow 0.22s ease !important;
}
div[data-testid="stTextInputRootElement"] input:focus {
    background: rgba(255,255,255,0.09) !important;
    border-color: rgba(167,139,250,0.75) !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.22) !important;
    outline: none !important;
}
div[data-testid="stTextInputRootElement"] input::placeholder {
    color: rgba(255,255,255,0.22) !important;
}
div[data-testid="stTextInputRootElement"] label {
    color: rgba(200,190,255,0.8) !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.4px !important;
}

/* Botão */
div.stButton > button {
    background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 12px !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.3px !important;
    width: 100% !important;
    padding: 0.68rem 1rem !important;
    box-shadow: 0 6px 22px -6px rgba(124,58,237,0.7) !important;
    transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease !important;
    animation: fadeSlideUp 0.8s cubic-bezier(0.16,1,0.3,1) 0.65s both;
}
div.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 30px -6px rgba(124,58,237,0.85) !important;
    filter: brightness(1.1) !important;
}
div.stButton > button:active {
    transform: translateY(0) !important;
    filter: brightness(0.95) !important;
}

/* Alertas */
div[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-size: 0.85rem !important;
    animation: fadeSlideUp 0.4s ease both;
}

/* Rodapé */
.hip-footer {
    text-align: center;
    margin-top: 1.8rem;
    font-size: 0.7rem;
    color: rgba(255,255,255,0.2);
    letter-spacing: 0.3px;
    animation: fadeIn 1s 1s both;
}
</style>
""", unsafe_allow_html=True)

# ─── Cabeçalho da marca (HTML puro) ────────────────────────────────
st.markdown(
    f"""
    <div class="hip-card">
      <div class="hip-logo">H</div>
      <div class="hip-brand-name">
        <div class="name">HIPNUS</div>
        <div class="sub">Cosméticos</div>
        <div class="tagline">{BRAND['tagline']}</div>
      </div>
      <div class="hip-divider"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─── Inputs de login ─────────────────────────────────────────────────
login_input = st.text_input("Usuário", placeholder="seu.usuario", key="_login")
senha_input = st.text_input("Senha", placeholder="••••••••", type="password", key="_senha")

st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

btn_entrar = st.button("→ Entrar na plataforma", use_container_width=True, type="primary")

# ─── Lógica ───────────────────────────────────────────────────────────────
if btn_entrar:
    if not login_input or not senha_input:
        st.warning("⚠️ Preencha usuário e senha.")
    else:
        ok, msg = fazer_login(login_input.strip(), senha_input)
        if ok:
            st.success(msg)
            st.switch_page("pages/0_🏠_Home.py")
        else:
            st.error("❌ " + msg)

# ─── Rodapé ───────────────────────────────────────────────────────────────
st.markdown(
    "<div class='hip-footer'>HIPNUS COSMÉTICOS &copy; 2026 &nbsp;·&nbsp; Plataforma exclusiva da marca.</div>",
    unsafe_allow_html=True,
)
