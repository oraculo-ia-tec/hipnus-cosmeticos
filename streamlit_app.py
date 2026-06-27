"""
streamlit_app.py — HIPNUS COSMÉTICOS  ·  Premium Neon Edition
==============================================================
Entrypoint do Streamlit Cloud — página de Login Premium.
Aceita login por USERNAME ou E-MAIL.
UI/UX Pro Max: fontes premium, neon glow, glassmorphism, animações, FAB.
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
frontend_path = _ROOT / "frontend"
if str(frontend_path) not in sys.path:
    sys.path.insert(0, str(frontend_path))
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from app.db.init_db import init_db
    init_db()
except Exception:
    pass

import streamlit as st

# ─── Limpeza de cache global no boot ──────────────────────────────────────
if not st.session_state.get("_cache_cleared"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.session_state["_cache_cleared"] = True

from lib.auth import fazer_login
from lib.theme import inject_theme, inject_login_style

st.set_page_config(
    page_title="Login — HIPNUS COSMÉTICOS",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_theme()
inject_login_style()

if st.session_state.get("autenticado"):
    st.switch_page("pages/1_Home.py")

st.html("""
<style>
/* ── Reset full-viewport ────────────────────────────────────── */
[data-testid="stMainBlockContainer"],
[data-testid="stMain"] > div,
.block-container {
  padding: 0 !important; max-width: 100% !important; margin: 0 !important;
}
[data-testid="stToolbar"],
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
header[data-testid="stHeader"] { display: none !important; }

/* ── Layout split ────────────────────────────────────────────── */
[data-testid="stHorizontalBlock"] {
  gap: 0 !important; align-items: stretch !important; min-height: 100vh !important;
}
[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
  padding: 0 !important; min-height: 100vh;
}

/* ── Painel Esquerdo — Neon Mesh ─────────────────────────────── */
[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child {
  background:
    radial-gradient(ellipse at 20% 20%, rgba(185,131,255,0.18) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(0,245,255,0.08) 0%, transparent 50%),
    radial-gradient(ellipse at 60% 10%, rgba(255,110,247,0.08) 0%, transparent 40%),
    linear-gradient(145deg, #0d0019 0%, #1a0733 35%, #2d1060 65%, #1a0733 100%);
  background-size: 100% 100%;
  position: relative;
  overflow: hidden;
}

/* ── Painel Direito — Clean Premium ─────────────────────────── */
[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:last-child {
  background: #faf9fd;
  display: flex; flex-direction: column;
  justify-content: center; padding: 48px 40px !important;
  position: relative;
}
[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:last-child::before {
  content: '';
  position: absolute; top: 0; left: 0;
  width: 1px; height: 100%;
  background: linear-gradient(180deg, transparent, rgba(185,131,255,0.4), transparent);
}

/* ── Inputs Premium ────────────────────────────────────────── */
[data-testid="stTextInput"] > div > div > input {
  background: #fff !important;
  border: 1.5px solid #e5e0f5 !important;
  border-radius: 14px !important;
  font-family: 'Inter', sans-serif !important;
  font-size: .95rem !important;
  padding: 14px 18px !important;
  color: #1a0a2e !important;
  transition: border-color .2s ease, box-shadow .2s ease !important;
  box-shadow: 0 2px 8px rgba(124,58,237,.04) !important;
}
[data-testid="stTextInput"] > div > div > input:focus {
  border-color: #7c3aed !important;
  box-shadow: 0 0 0 4px rgba(124,58,237,.1), 0 0 20px rgba(185,131,255,.12) !important;
  outline: none !important;
}
[data-testid="stTextInput"] > label {
  font-family: 'Inter', sans-serif !important;
  font-size: .78rem !important; font-weight: 600 !important;
  color: #6b5d8a !important; letter-spacing: .4px !important;
  text-transform: uppercase !important;
}

/* ── Botão Entrar — Neon Gradient ───────────────────────────── */
[data-testid="stButton"] > button[kind="primary"] {
  background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 60%, #7c3aed 100%) !important;
  background-size: 200% 100% !important;
  border: none !important; border-radius: 14px !important; height: 52px !important;
  font-family: 'Inter', sans-serif !important;
  font-size: .97rem !important; font-weight: 700 !important;
  letter-spacing: .4px !important; color: #fff !important;
  box-shadow: 0 4px 24px rgba(124,58,237,.4), 0 0 0 1px rgba(185,131,255,.2) !important;
  transition: all .25s cubic-bezier(0.16,1,0.3,1) !important;
  width: 100% !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
  background-position: right center !important;
  box-shadow: 0 8px 40px rgba(124,58,237,.55), 0 0 40px rgba(185,131,255,.25) !important;
  transform: translateY(-2px) !important;
}
[data-testid="stButton"] > button[kind="primary"]:active {
  transform: translateY(0px) !important;
}

/* ── Botão Demo ──────────────────────────────────────────────── */
[data-testid="stButton"] > button:not([kind="primary"]) {
  background: #fff !important;
  border: 1.5px solid #e5e0f5 !important;
  border-radius: 14px !important; height: 48px !important;
  font-family: 'Inter', sans-serif !important;
  font-size: .88rem !important; font-weight: 600 !important;
  color: #7c3aed !important;
  transition: all .2s ease !important; width: 100% !important;
}
[data-testid="stButton"] > button:not([kind="primary"]):hover {
  background: #f3f0ff !important;
  border-color: rgba(124,58,237,.35) !important;
  box-shadow: 0 0 20px rgba(185,131,255,.15) !important;
}

/* ── Animações login ────────────────────────────────────────────── */
@keyframes fadeSlideRight {
  from { opacity: 0; transform: translateX(-32px); }
  to   { opacity: 1; transform: translateX(0); }
}
@keyframes fadeSlideLeft {
  from { opacity: 0; transform: translateX(32px); }
  to   { opacity: 1; transform: translateX(0); }
}
@keyframes floatOrb {
  0%, 100% { transform: translateY(0) scale(1); opacity: .6; }
  50%       { transform: translateY(-20px) scale(1.05); opacity: .9; }
}
@keyframes spinRing {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
@keyframes shimmerBorder {
  0%   { background-position: -200% center; }
  100% { background-position:  200% center; }
}
</style>
""")

col_left, col_right = st.columns([55, 45], gap="small")

with col_left:
    st.html("""
    <style>
    [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child
    [data-testid="stHtml"] { height: 100%; }

    /* ── Orbes decorativos ────────────────── */
    .hip-orb {
      position: absolute; border-radius: 50%;
      filter: blur(60px); pointer-events: none;
    }
    .hip-orb-1 {
      width: 380px; height: 380px;
      top: -80px; left: -80px;
      background: radial-gradient(circle, rgba(185,131,255,0.2) 0%, transparent 70%);
      animation: floatOrb 8s ease-in-out infinite;
    }
    .hip-orb-2 {
      width: 280px; height: 280px;
      bottom: 40px; right: -60px;
      background: radial-gradient(circle, rgba(0,245,255,0.12) 0%, transparent 70%);
      animation: floatOrb 11s ease-in-out infinite reverse;
    }
    .hip-orb-3 {
      width: 200px; height: 200px;
      top: 50%; left: 50%;
      background: radial-gradient(circle, rgba(255,110,247,0.08) 0%, transparent 70%);
      animation: floatOrb 14s ease-in-out infinite 2s;
    }

    /* ── Grid de pontos ─────────────────── */
    .hip-dot-grid {
      position: absolute; inset: 0;
      background-image: radial-gradient(rgba(185,131,255,0.15) 1px, transparent 1px);
      background-size: 32px 32px;
      pointer-events: none;
      mask-image: radial-gradient(ellipse 80% 80% at 50% 50%, black 40%, transparent 100%);
    }

    /* ── Anel giratório decorativo ────────── */
    .hip-ring {
      position: absolute;
      top: 50%; left: 50%;
      width: 500px; height: 500px;
      margin: -250px 0 0 -250px;
      border-radius: 50%;
      border: 1px solid rgba(185,131,255,0.06);
      animation: spinRing 40s linear infinite;
      pointer-events: none;
    }
    .hip-ring::before {
      content: '';
      position: absolute;
      top: 0; left: 50%;
      width: 6px; height: 6px; margin-left: -3px;
      border-radius: 50%;
      background: rgba(185,131,255,0.5);
      box-shadow: 0 0 12px rgba(185,131,255,0.8);
    }
    .hip-ring-2 {
      width: 360px; height: 360px;
      margin: -180px 0 0 -180px;
      border-color: rgba(0,245,255,0.04);
      animation: spinRing 28s linear infinite reverse;
    }

    /* ── Painel principal ────────────────── */
    .hip-panel-inner {
      min-height: 100vh; padding: 52px 52px;
      display: flex; flex-direction: column; justify-content: space-between;
      position: relative; overflow: hidden;
      animation: fadeSlideRight 0.75s cubic-bezier(0.16,1,0.3,1) both;
    }

    /* ── Logo row ─────────────────────── */
    .hip-logo-row { display: flex; align-items: center; gap: 14px; position: relative; z-index: 2; }
    .hip-logo-icon {
      width: 50px; height: 50px; border-radius: 15px;
      background: linear-gradient(135deg, rgba(185,131,255,0.2) 0%, rgba(124,58,237,0.3) 100%);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(185,131,255,0.35);
      display: flex; align-items: center; justify-content: center;
      font-family: 'Playfair Display', serif;
      font-weight: 900; font-size: 1.45rem; color: #fff;
      letter-spacing: -1px; flex-shrink: 0;
      box-shadow: 0 0 20px rgba(185,131,255,0.3), inset 0 1px 0 rgba(255,255,255,0.1);
    }
    .hip-logo-text .brand-name {
      font-family: 'Playfair Display', serif;
      font-weight: 800; font-size: 1.1rem;
      background: linear-gradient(90deg, #fff 0%, rgba(185,131,255,0.9) 100%);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
      letter-spacing: -.3px; line-height: 1.1;
    }
    .hip-logo-text .brand-sub  {
      font-size: .62rem; color: rgba(185,131,255,.55);
      letter-spacing: 3px; text-transform: uppercase;
    }

    /* ── Hero block ────────────────────── */
    .hip-hero-block { padding: 0 0 16px; position: relative; z-index: 2; }
    .kicker-pill {
      display: inline-flex; align-items: center; gap: 6px;
      background: rgba(185,131,255,.1);
      border: 1px solid rgba(185,131,255,.25);
      color: rgba(185,131,255,.9);
      font-family: 'Inter', sans-serif;
      font-size: .64rem; font-weight: 700; letter-spacing: 2.5px; text-transform: uppercase;
      padding: 6px 16px; border-radius: 999px; margin-bottom: 28px;
    }
    .kicker-pill::before {
      content: '';
      width: 6px; height: 6px; border-radius: 50%;
      background: rgba(185,131,255,0.8);
      box-shadow: 0 0 8px rgba(185,131,255,0.8);
      flex-shrink: 0;
    }
    .hip-hero-block h1 {
      font-family: 'Playfair Display', serif;
      font-size: clamp(2rem, 2.8vw, 3.2rem);
      font-weight: 900; color: #fff;
      line-height: 1.15; letter-spacing: -.5px; margin: 0 0 20px;
    }
    .hip-hero-block h1 span {
      background: linear-gradient(90deg, #e2b4ff 0%, #b983ff 40%, #00f5ff 100%);
      background-size: 200% auto;
      -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
      animation: shimmerBorder 4s linear infinite;
    }
    .hip-hero-block p {
      color: rgba(255,255,255,.65); font-family: 'Inter', sans-serif;
      font-size: .95rem; line-height: 1.7; max-width: 40ch; margin: 0 0 36px;
    }

    /* ── Claims ────────────────────────── */
    .claims { display: flex; flex-direction: column; gap: 16px; }
    .claim  { display: flex; align-items: flex-start; gap: 14px; }
    .claim-icon {
      width: 38px; height: 38px; border-radius: 12px; flex-shrink: 0;
      background: rgba(185,131,255,.1);
      border: 1px solid rgba(185,131,255,.2);
      display: flex; align-items: center; justify-content: center;
      font-size: 1.1rem;
      box-shadow: 0 0 12px rgba(185,131,255,0.1);
      transition: all .2s ease;
    }
    .claim:hover .claim-icon {
      background: rgba(185,131,255,.2);
      border-color: rgba(185,131,255,.4);
      box-shadow: 0 0 20px rgba(185,131,255,0.25);
    }
    .claim-text { font-family: 'Inter', sans-serif; font-size: .85rem; color: rgba(255,255,255,.65); font-weight: 400; line-height: 1.4; }
    .claim-text strong { color: rgba(255,255,255,.92); font-weight: 700; display: block; font-size: .9rem; margin-bottom: 2px; }

    /* ── Linha separadora com gradiente ────── */
    .hip-line-sep {
      height: 1px;
      background: linear-gradient(90deg, transparent, rgba(185,131,255,0.35), rgba(0,245,255,0.15), transparent);
      margin: 32px 0;
      position: relative; z-index: 2;
    }

    /* ── Stats row ─────────────────────── */
    .hip-stats-row {
      display: flex; gap: 24px;
      position: relative; z-index: 2;
    }
    .hip-mini-stat .v {
      font-family: 'Playfair Display', serif;
      font-size: 1.5rem; font-weight: 800; color: #fff;
      line-height: 1;
    }
    .hip-mini-stat .v span {
      background: linear-gradient(90deg, #b983ff, #00f5ff);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    }
    .hip-mini-stat .l { font-size: .68rem; color: rgba(185,131,255,.6); letter-spacing: 1px; text-transform: uppercase; margin-top: 2px; }

    /* ── Footer ────────────────────────── */
    .hip-panel-footer {
      font-family: 'Inter', sans-serif;
      font-size: .66rem; color: rgba(185,131,255,.3);
      letter-spacing: .8px;
      position: relative; z-index: 2;
    }
    </style>

    <div class="hip-panel-inner">
      <!-- Orbes e decoração -->  
      <div class="hip-orb hip-orb-1"></div>
      <div class="hip-orb hip-orb-2"></div>
      <div class="hip-orb hip-orb-3"></div>
      <div class="hip-dot-grid"></div>
      <div class="hip-ring"></div>
      <div class="hip-ring hip-ring-2"></div>

      <!-- Logo -->
      <div class="hip-logo-row">
        <div class="hip-logo-icon">H</div>
        <div class="hip-logo-text">
          <div class="brand-name">HIPNUS</div>
          <div class="brand-sub">Cosméticos</div>
        </div>
      </div>

      <!-- Hero -->
      <div class="hip-hero-block">
        <div class="kicker-pill">Plataforma Exclusiva B2B</div>
        <h1>Sua vitrine capilar<br><span>profissional</span></h1>
        <p>Acesse o catálogo completo, gerencie pedidos e explore condições exclusivas para parceiros e distribuidores Hipnus.</p>
        <div class="claims">
          <div class="claim">
            <div class="claim-icon">📦</div>
            <div class="claim-text"><strong>Catálogo completo</strong>Todas as linhas, máscaras e tratamentos capilares</div>
          </div>
          <div class="claim">
            <div class="claim-icon">🏪</div>
            <div class="claim-text"><strong>Loja do Parceiro B2B</strong>Preços exclusivos para profissionais e revendedores</div>
          </div>
          <div class="claim">
            <div class="claim-icon">⚡</div>
            <div class="claim-text"><strong>Pedidos em tempo real</strong>Acompanhe do carrinho à entrega</div>
          </div>
        </div>
      </div>

      <!-- Linha + Stats -->
      <div>
        <div class="hip-line-sep"></div>
        <div class="hip-stats-row">
          <div class="hip-mini-stat">
            <div class="v"><span>+500</span></div>
            <div class="l">Produtos</div>
          </div>
          <div class="hip-mini-stat">
            <div class="v"><span>B2B</span></div>
            <div class="l">Plataforma</div>
          </div>
          <div class="hip-mini-stat">
            <div class="v"><span>24/7</span></div>
            <div class="l">Disponível</div>
          </div>
        </div>
      </div>

      <div class="hip-panel-footer">&copy; 2026 HIPNUS COSMÉTICOS &mdash; Todos os direitos reservados</div>
    </div>
    """)

with col_right:
    st.html("""
    <style>
    .hip-form-header {
      max-width: 380px; margin: 0 auto 32px;
      animation: fadeSlideLeft 0.65s 0.1s cubic-bezier(0.16,1,0.3,1) both;
    }
    .hip-eyebrow {
      display: flex; align-items: center; gap: 10px;
      font-family: 'Inter', sans-serif;
      font-size: .7rem; font-weight: 700;
      color: #7c3aed; letter-spacing: 2px; text-transform: uppercase;
      margin-bottom: 10px;
    }
    .hip-eyebrow span {
      display: inline-block; width: 22px; height: 2px;
      background: linear-gradient(90deg, #7c3aed, #b983ff);
      border-radius: 1px;
      box-shadow: 0 0 6px rgba(124,58,237,0.6);
    }
    .hip-form-header h2 {
      font-family: 'Playfair Display', serif;
      font-size: 1.65rem; font-weight: 800;
      color: #1a0a2e; letter-spacing: -.5px; line-height: 1.2; margin: 0 0 8px;
    }
    .hip-form-header p {
      font-family: 'Inter', sans-serif;
      font-size: .85rem; color: #6b7280; line-height: 1.55; margin: 0;
    }
    /* Anel decorativo topo direito */
    .hip-corner-ring {
      position: absolute; top: -80px; right: -80px;
      width: 220px; height: 220px; border-radius: 50%;
      border: 1px solid rgba(124,58,237,0.08);
      pointer-events: none;
    }
    .hip-corner-ring::before {
      content: '';
      position: absolute; top: 20px; left: 20px; right: 20px; bottom: 20px;
      border-radius: 50%;
      border: 1px solid rgba(185,131,255,0.06);
    }
    </style>

    <div class="hip-corner-ring"></div>

    <div class="hip-form-header">
      <div class="hip-eyebrow"><span></span>Bem-vindo de volta</div>
      <h2>Entrar na plataforma</h2>
      <p>Use seu usuário <strong>ou e-mail</strong> e senha para acessar sua conta.</p>
    </div>
    """)

    login_input = st.text_input(
        "Usuário ou e-mail",
        placeholder="usuario  ou  seu@email.com",
        key="_login",
    )
    senha_input = st.text_input("Senha", placeholder="••••••••", type="password", key="_senha")
    st.write("")

    btn_entrar = st.button("Entrar  →", use_container_width=True, type="primary", key="btn_entrar")

    st.html('<div style="display:flex;align-items:center;gap:10px;margin:14px 0;color:#c4bfd8;font-family:\'Inter\',sans-serif;font-size:.75rem;"><span style="flex:1;height:1px;background:linear-gradient(90deg,transparent,#ede9f8);display:block"></span>ou<span style="flex:1;height:1px;background:linear-gradient(270deg,transparent,#ede9f8);display:block"></span></div>')

    btn_demo = st.button("❖ Acessar modo demonstração", use_container_width=True, key="btn_demo",
                         help="Entra sem cadastro para explorar a plataforma.")

    st.html("""
    <div style="text-align:center;margin-top:32px;">
      <div style="font-family:'Inter',sans-serif;font-size:.68rem;color:#c4bfd8;line-height:1.8;">
        HIPNUS COSMÉTICOS &copy; 2026<br>
        <span style="color:#d8b4fe;">Plataforma exclusiva da marca</span> &mdash; Acesso restrito
      </div>
      <div style="margin-top:12px;display:flex;justify-content:center;gap:6px;">
        <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#7c3aed;box-shadow:0 0 8px rgba(124,58,237,0.8);"></span>
        <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#b983ff;box-shadow:0 0 8px rgba(185,131,255,0.8);"></span>
        <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#00f5ff;box-shadow:0 0 8px rgba(0,245,255,0.6);"></span>
      </div>
    </div>
    """)

if btn_entrar:
    if not login_input or not senha_input:
        with col_right:
            st.warning("⚠️ Preencha o usuário/e-mail e a senha para continuar.")
    else:
        ok, msg = fazer_login(login_input.strip(), senha_input)
        if ok:
            st.switch_page("pages/1_Home.py")
        else:
            with col_right:
                st.error(f"❌ {msg}")

if btn_demo:
    st.session_state.update({
        "autenticado": True, "usuario": "demo", "perfil": "demo",
        "nome": "Visitante", "display_name": "Modo demonstração",
        "email": "", "token": None, "via_api": False,
    })
    st.switch_page("pages/1_Home.py")
