"""
streamlit_app.py — HIPNUS COSMÉTICOS
======================================
Entrypoint do Streamlit Cloud — página de Login.
Aceita login por USERNAME ou E-MAIL.
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
[data-testid="stMainBlockContainer"],
[data-testid="stMain"] > div,
.block-container {
  padding: 0 !important; max-width: 100% !important; margin: 0 !important;
}
[data-testid="stToolbar"],
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
header[data-testid="stHeader"] { display: none !important; }
[data-testid="stHorizontalBlock"] {
  gap: 0 !important; align-items: stretch !important; min-height: 100vh !important;
}
[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
  padding: 0 !important; min-height: 100vh;
}
[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child {
  background: linear-gradient(145deg, #1a0733 0%, #3b1278 40%, #6c2bd9 75%, #8b44f6 100%);
}
[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:last-child {
  background: #f8f7fc; display: flex; flex-direction: column;
  justify-content: center; padding: 48px 40px !important;
}
[data-testid="stTextInput"] > div > div > input {
  background: #fff !important; border: 1.5px solid #e5e0f5 !important;
  border-radius: 12px !important; font-size: .96rem !important;
  padding: 13px 16px !important; color: #1a0a2e !important;
  transition: border-color .18s, box-shadow .18s !important;
}
[data-testid="stTextInput"] > div > div > input:focus {
  border-color: #7c3aed !important;
  box-shadow: 0 0 0 4px rgba(124,58,237,.12) !important; outline: none !important;
}
[data-testid="stTextInput"] > label {
  font-size: .8rem !important; font-weight: 600 !important;
  color: #4b4567 !important; letter-spacing: .2px !important;
}
[data-testid="stButton"] > button[kind="primary"] {
  background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%) !important;
  border: none !important; border-radius: 12px !important; height: 50px !important;
  font-size: .97rem !important; font-weight: 700 !important;
  letter-spacing: .3px !important; color: #fff !important;
  box-shadow: 0 4px 20px rgba(124,58,237,.35) !important;
  transition: all .18s cubic-bezier(0.16,1,0.3,1) !important; width: 100% !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
  box-shadow: 0 8px 28px rgba(124,58,237,.45) !important; transform: translateY(-1px) !important;
}
[data-testid="stButton"] > button:not([kind="primary"]) {
  background: #fff !important; border: 1.5px solid #e5e0f5 !important;
  border-radius: 12px !important; height: 46px !important;
  font-size: .87rem !important; font-weight: 600 !important;
  color: #7c3aed !important; transition: all .18s ease !important; width: 100% !important;
}
[data-testid="stButton"] > button:not([kind="primary"]):hover {
  background: #f3f0ff !important; border-color: #7c3aed !important;
}
@keyframes fadeSlideRight {
  from { opacity: 0; transform: translateX(-24px); }
  to   { opacity: 1; transform: translateX(0); }
}
@keyframes fadeSlideLeft {
  from { opacity: 0; transform: translateX(24px); }
  to   { opacity: 1; transform: translateX(0); }
}
</style>
""")

col_left, col_right = st.columns([55, 45], gap="small")

with col_left:
    st.html("""
    <style>
    [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child
    [data-testid="stHtml"] { height: 100%; }
    .hip-panel-inner {
      min-height: 100vh; padding: 56px 48px;
      display: flex; flex-direction: column; justify-content: space-between;
      position: relative; overflow: hidden;
      animation: fadeSlideRight 0.7s cubic-bezier(0.16,1,0.3,1) both;
    }
    .hip-panel-inner::before {
      content: ""; position: absolute; top: -120px; right: -120px;
      width: 420px; height: 420px; border-radius: 50%;
      background: rgba(255,255,255,0.04); pointer-events: none;
    }
    .hip-panel-inner::after {
      content: ""; position: absolute; bottom: -80px; left: -80px;
      width: 300px; height: 300px; border-radius: 50%;
      background: rgba(255,255,255,0.03); pointer-events: none;
    }
    .hip-logo-row { display: flex; align-items: center; gap: 14px; }
    .hip-logo-icon {
      width: 48px; height: 48px; border-radius: 14px;
      background: rgba(255,255,255,0.15); backdrop-filter: blur(10px);
      border: 1px solid rgba(255,255,255,0.25);
      display: flex; align-items: center; justify-content: center;
      font-weight: 900; font-size: 1.4rem; color: #fff; letter-spacing: -1px; flex-shrink: 0;
    }
    .hip-logo-text .brand-name { font-weight: 800; font-size: 1.05rem; color: #fff; letter-spacing: -.3px; line-height: 1.1; }
    .hip-logo-text .brand-sub  { font-size: .62rem; color: rgba(255,255,255,.55); letter-spacing: 2.5px; text-transform: uppercase; }
    .hip-hero-block { padding: 0 0 16px; }
    .kicker-pill {
      display: inline-block; background: rgba(255,255,255,.12);
      border: 1px solid rgba(255,255,255,.2); color: rgba(255,255,255,.85);
      font-size: .66rem; font-weight: 700; letter-spacing: 2px; text-transform: uppercase;
      padding: 5px 14px; border-radius: 999px; margin-bottom: 22px;
    }
    .hip-hero-block h1 {
      font-size: clamp(1.8rem, 2.5vw, 2.8rem); font-weight: 800;
      color: #fff; line-height: 1.2; letter-spacing: -.5px; margin: 0 0 18px;
    }
    .hip-hero-block h1 span {
      background: linear-gradient(90deg, #e2b4ff, #b983ff);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    }
    .hip-hero-block p { color: rgba(255,255,255,.7); font-size: .95rem; line-height: 1.65; max-width: 38ch; margin: 0 0 32px; }
    .claims { display: flex; flex-direction: column; gap: 14px; }
    .claim  { display: flex; align-items: center; gap: 12px; }
    .claim-icon {
      width: 34px; height: 34px; border-radius: 10px;
      background: rgba(255,255,255,.1); border: 1px solid rgba(255,255,255,.18);
      display: flex; align-items: center; justify-content: center;
      font-size: 1rem; flex-shrink: 0;
    }
    .claim-text { font-size: .85rem; color: rgba(255,255,255,.8); font-weight: 500; line-height: 1.35; }
    .claim-text strong { color: #fff; font-weight: 700; display: block; font-size: .88rem; }
    .hip-panel-footer { font-size: .68rem; color: rgba(255,255,255,.35); letter-spacing: .5px; }
    </style>
    <div class="hip-panel-inner">
      <div class="hip-logo-row">
        <div class="hip-logo-icon">H</div>
        <div class="hip-logo-text">
          <div class="brand-name">HIPNUS</div>
          <div class="brand-sub">Cosméticos</div>
        </div>
      </div>
      <div class="hip-hero-block">
        <div class="kicker-pill">Plataforma Exclusiva</div>
        <h1>Sua vitrine capilar<br><span>profissional</span></h1>
        <p>Acesse o catálogo completo, gerencie pedidos e explore condições exclusivas para parceiros e distribuidores Hipnus.</p>
        <div class="claims">
          <div class="claim">
            <div class="claim-icon">📦</div>
            <div class="claim-text"><strong>Catálogo completo</strong>Todas as linhas, máscaras e tratamentos</div>
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
      <div class="hip-panel-footer">&copy; 2026 HIPNUS COSMÉTICOS &mdash; Todos os direitos reservados</div>
    </div>
    """)

with col_right:
    st.html("""
    <div style="margin:0 auto 28px;max-width:360px;animation:fadeSlideLeft 0.6s 0.15s cubic-bezier(0.16,1,0.3,1) both;">
      <div style="font-size:.72rem;font-weight:700;color:#7c3aed;letter-spacing:1.5px;text-transform:uppercase;
                  margin-bottom:8px;display:flex;align-items:center;gap:8px;">
        <span style="display:inline-block;width:18px;height:2px;background:#7c3aed;border-radius:1px;"></span>
        Bem-vindo de volta
      </div>
      <h2 style="font-size:1.55rem;font-weight:800;color:#1a0a2e;letter-spacing:-.5px;line-height:1.2;margin:0 0 7px;">
        Entrar na plataforma
      </h2>
      <p style="font-size:.85rem;color:#6b7280;line-height:1.5;margin:0;">Use seu usuário <strong>ou e-mail</strong> e senha para acessar.</p>
    </div>
    """)

    # Campo aceita username OU e-mail
    login_input = st.text_input(
        "Usuário ou e-mail",
        placeholder="usuario  ou  seu@email.com",
        key="_login",
    )
    senha_input = st.text_input("Senha", placeholder="••••••••", type="password", key="_senha")
    st.write("")

    btn_entrar = st.button("Entrar  →", use_container_width=True, type="primary", key="btn_entrar")

    st.html('<div style="display:flex;align-items:center;gap:10px;margin:10px 0;color:#c4bfd8;font-size:.75rem;"><span style="flex:1;height:1px;background:#ede9f8;display:block"></span>ou<span style="flex:1;height:1px;background:#ede9f8;display:block"></span></div>')

    btn_demo = st.button("Acessar modo demonstração", use_container_width=True, key="btn_demo",
                         help="Entra sem cadastro para explorar a plataforma.")

    st.html('<div style="text-align:center;margin-top:24px;font-size:.7rem;color:#b0a9c8;line-height:1.7;">HIPNUS COSMÉTICOS &copy; 2026<br>Plataforma exclusiva da marca. Acesso restrito.</div>')

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
