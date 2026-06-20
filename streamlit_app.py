"""
streamlit_app.py — HIPNUS COSMÉTICOS
======================================
Entrypoint do Streamlit Cloud — página de Login.

Navegação:
  Login bem-sucedido  →  st.switch_page("pages/1_Home.py")
  require_auth() fail →  st.switch_page("streamlit_app.py")
  logout()            →  st.switch_page("streamlit_app.py")

Layout: split-screen full-viewport.
  Coluna esquerda  — painel visual da marca (gradient + claims)
  Coluna direita   — formulário de login centralizado
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

# ─ Configuração da página ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Login — HIPNUS COSMÉTICOS",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_theme()
inject_login_style()

# ─ Redireciona se já autenticado ─────────────────────────────────────────────────
if st.session_state.get("autenticado"):
    st.switch_page("pages/1_Home.py")

# ─ Painel esquerdo: visual da marca (HTML puro, sem Streamlit widgets) ───────
st.html(f"""
<style>
  /* ── Reset do layout Streamlit para o login split-screen ──────────────── */
  [data-testid="stMainBlockContainer"] {{
    padding: 0 !important;
    max-width: 100% !important;
  }}
  [data-testid="stMain"] > div {{
    padding: 0 !important;
  }}
  [data-testid="stHorizontalBlock"] {{
    gap: 0 !important;
    align-items: stretch !important;
  }}
  /* Esconde a barra superior do Streamlit */
  [data-testid="stToolbar"] {{ display: none !important; }}

  /* ── Painel esquerdo ───────────────────────────────────────────────── */
  .hip-login-panel-left {{
    background: linear-gradient(145deg, #1a0733 0%, #3b1278 40%, #6c2bd9 75%, #8b44f6 100%);
    min-height: 100vh;
    padding: 56px 48px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
    animation: fadeSlideRight 0.7s cubic-bezier(0.16,1,0.3,1) both;
  }}
  .hip-login-panel-left::before {{
    content: "";
    position: absolute;
    top: -120px; right: -120px;
    width: 400px; height: 400px;
    border-radius: 50%;
    background: rgba(255,255,255,0.04);
    pointer-events: none;
  }}
  .hip-login-panel-left::after {{
    content: "";
    position: absolute;
    bottom: -80px; left: -80px;
    width: 300px; height: 300px;
    border-radius: 50%;
    background: rgba(255,255,255,0.03);
    pointer-events: none;
  }}

  /* Logo no painel esquerdo */
  .hip-left-logo {{
    display: flex;
    align-items: center;
    gap: 14px;
    animation: fadeSlideRight 0.6s 0.1s cubic-bezier(0.16,1,0.3,1) both;
  }}
  .hip-left-logo-icon {{
    width: 48px; height: 48px;
    border-radius: 14px;
    background: rgba(255,255,255,0.15);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.25);
    display: flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 1.4rem;
    color: #fff;
    letter-spacing: -1px;
    flex-shrink: 0;
  }}
  .hip-left-logo-text .brand-name {{
    font-weight: 800; font-size: 1.05rem;
    color: #fff; letter-spacing: -.3px; line-height: 1.1;
  }}
  .hip-left-logo-text .brand-sub {{
    font-size: .62rem; color: rgba(255,255,255,.55);
    letter-spacing: 2.5px; text-transform: uppercase;
  }}

  /* Hero text no painel esquerdo */
  .hip-left-hero {{
    padding: 0 0 16px;
    animation: fadeSlideRight 0.6s 0.2s cubic-bezier(0.16,1,0.3,1) both;
  }}
  .hip-left-hero .kicker {{
    display: inline-block;
    background: rgba(255,255,255,.12);
    border: 1px solid rgba(255,255,255,.2);
    color: rgba(255,255,255,.85);
    font-size: .66rem; font-weight: 700;
    letter-spacing: 2px; text-transform: uppercase;
    padding: 5px 14px;
    border-radius: 999px;
    margin-bottom: 22px;
  }}
  .hip-left-hero h1 {{
    font-size: clamp(1.8rem, 3vw, 2.8rem);
    font-weight: 800;
    color: #fff;
    line-height: 1.2;
    letter-spacing: -.5px;
    margin: 0 0 18px;
  }}
  .hip-left-hero h1 span {{
    background: linear-gradient(90deg, #e2b4ff, #b983ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }}
  .hip-left-hero p {{
    color: rgba(255,255,255,.7);
    font-size: .95rem;
    line-height: 1.65;
    max-width: 38ch;
    margin: 0 0 32px;
  }}

  /* Claims / bullets */
  .hip-left-claims {{
    display: flex; flex-direction: column; gap: 14px;
    animation: fadeSlideRight 0.6s 0.3s cubic-bezier(0.16,1,0.3,1) both;
  }}
  .hip-left-claim {{
    display: flex; align-items: center; gap: 12px;
  }}
  .hip-left-claim .claim-icon {{
    width: 34px; height: 34px;
    border-radius: 10px;
    background: rgba(255,255,255,.1);
    border: 1px solid rgba(255,255,255,.18);
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
  }}
  .hip-left-claim .claim-text {{
    font-size: .85rem; color: rgba(255,255,255,.8);
    font-weight: 500; line-height: 1.35;
  }}
  .hip-left-claim .claim-text strong {{
    color: #fff; font-weight: 700;
    display: block; font-size: .88rem;
  }}

  /* Footer do painel esquerdo */
  .hip-left-footer {{
    font-size: .68rem; color: rgba(255,255,255,.35);
    letter-spacing: .5px;
    animation: fadeSlideRight 0.6s 0.4s cubic-bezier(0.16,1,0.3,1) both;
  }}

  /* ── Painel direito ───────────────────────────────────────────────── */
  .hip-login-panel-right {{
    background: #f8f7fc;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 48px 32px;
    animation: fadeSlideLeft 0.7s cubic-bezier(0.16,1,0.3,1) both;
  }}
  .hip-login-form-wrap {{
    width: 100%;
    max-width: 400px;
  }}

  /* Cabeçalho do form */
  .hip-form-header {{
    margin-bottom: 32px;
    animation: fadeSlideLeft 0.6s 0.15s cubic-bezier(0.16,1,0.3,1) both;
  }}
  .hip-form-header .welcome {{
    font-size: .78rem; font-weight: 700;
    color: #7c3aed;
    letter-spacing: 1.5px; text-transform: uppercase;
    margin-bottom: 8px;
    display: flex; align-items: center; gap: 8px;
  }}
  .hip-form-header .welcome::before {{
    content: "";
    display: inline-block;
    width: 20px; height: 2px;
    background: #7c3aed;
    border-radius: 1px;
  }}
  .hip-form-header h2 {{
    font-size: 1.65rem; font-weight: 800;
    color: #1a0a2e;
    letter-spacing: -.5px; line-height: 1.2;
    margin: 0 0 8px;
  }}
  .hip-form-header p {{
    font-size: .88rem; color: #6b7280;
    line-height: 1.5; margin: 0;
  }}

  /* ── Animações ──────────────────────────────────────────────────────────────── */
  @keyframes fadeSlideRight {{
    from {{ opacity: 0; transform: translateX(-24px); }}
    to   {{ opacity: 1; transform: translateX(0); }}
  }}
  @keyframes fadeSlideLeft {{
    from {{ opacity: 0; transform: translateX(24px); }}
    to   {{ opacity: 1; transform: translateX(0); }}
  }}

  /* ── Estilo dos inputs Streamlit no context do form ─────────────────── */
  [data-testid="stTextInput"] > div > div > input {{
    background: #fff !important;
    border: 1.5px solid #e5e0f5 !important;
    border-radius: 12px !important;
    font-size: .96rem !important;
    padding: 14px 16px !important;
    color: #1a0a2e !important;
    transition: border-color .18s, box-shadow .18s !important;
  }}
  [data-testid="stTextInput"] > div > div > input:focus {{
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 4px rgba(124,58,237,.12) !important;
    outline: none !important;
  }}
  [data-testid="stTextInput"] > label {{
    font-size: .8rem !important;
    font-weight: 600 !important;
    color: #4b4567 !important;
    letter-spacing: .2px !important;
    margin-bottom: 4px !important;
  }}

  /* Botão Entrar */
  [data-testid="stButton"] > button[kind="primary"] {{
    background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%) !important;
    border: none !important;
    border-radius: 12px !important;
    height: 50px !important;
    font-size: .97rem !important;
    font-weight: 700 !important;
    letter-spacing: .3px !important;
    color: #fff !important;
    box-shadow: 0 4px 20px rgba(124,58,237,.35) !important;
    transition: all .18s cubic-bezier(0.16,1,0.3,1) !important;
  }}
  [data-testid="stButton"] > button[kind="primary"]:hover {{
    box-shadow: 0 8px 28px rgba(124,58,237,.45) !important;
    transform: translateY(-1px) !important;
  }}

  /* Botão Demo */
  [data-testid="stButton"] > button:not([kind="primary"]) {{
    background: #fff !important;
    border: 1.5px solid #e5e0f5 !important;
    border-radius: 12px !important;
    height: 50px !important;
    font-size: .88rem !important;
    font-weight: 600 !important;
    color: #7c3aed !important;
    transition: all .18s ease !important;
  }}
  [data-testid="stButton"] > button:not([kind="primary"]):hover {{
    background: #f3f0ff !important;
    border-color: #7c3aed !important;
  }}

  /* Divisór label "ou" */
  .hip-or-divider {{
    display: flex; align-items: center; gap: 12px;
    margin: 4px 0;
    color: #9ca3af; font-size: .78rem;
  }}
  .hip-or-divider::before, .hip-or-divider::after {{
    content: ""; flex: 1;
    height: 1px; background: #e8e4f5;
  }}

  /* Footer do form */
  .hip-right-footer {{
    text-align: center;
    margin-top: 28px;
    font-size: .72rem;
    color: #9ca3af;
    line-height: 1.7;
    animation: fadeSlideLeft 0.6s 0.5s cubic-bezier(0.16,1,0.3,1) both;
  }}

  /* ── Responsivo: colapsa para uma coluna em mobile ─────────────────── */
  @media (max-width: 768px) {{
    .hip-login-panel-left {{
      display: none;
    }}
    .hip-login-panel-right {{
      padding: 40px 20px;
    }}
  }}
</style>

<!-- Painel esquerdo: visual da marca -->
<div class="hip-login-panel-left">
  <div class="hip-left-logo">
    <div class="hip-left-logo-icon">H</div>
    <div class="hip-left-logo-text">
      <div class="brand-name">HIPNUS</div>
      <div class="brand-sub">Cosméticos</div>
    </div>
  </div>

  <div class="hip-left-hero">
    <div class="kicker">Plataforma Exclusiva</div>
    <h1>Sua vitrine capilar<br><span>profissional</span></h1>
    <p>Acesse o catálogo completo, gerencie pedidos e explore condições exclusivas para parceiros e distribuidores Hipnus.</p>

    <div class="hip-left-claims">
      <div class="hip-left-claim">
        <div class="claim-icon">📦</div>
        <div class="claim-text">
          <strong>Catálogo completo</strong>
          Todas as linhas, máscaras e tratamentos
        </div>
      </div>
      <div class="hip-left-claim">
        <div class="claim-icon">🏪</div>
        <div class="claim-text">
          <strong>Loja do Parceiro B2B</strong>
          Preços exclusivos para profissionais e revendedores
        </div>
      </div>
      <div class="hip-left-claim">
        <div class="claim-icon">⚡</div>
        <div class="claim-text">
          <strong>Pedidos em tempo real</strong>
          Acompanhe do carrinho à entrega
        </div>
      </div>
    </div>
  </div>

  <div class="hip-left-footer">
    &copy; 2026 HIPNUS COSMÉTICOS &mdash; Todos os direitos reservados
  </div>
</div>
""")

# ─ Painel direito: formulário (widgets Streamlit) ────────────────────────
# Injetamos um wrapper div que o Streamlit renderiza dentro do layout wide
st.html("""
<div class="hip-login-panel-right" id="hip-right-panel">
  <div class="hip-login-form-wrap">
    <div class="hip-form-header">
      <div class="welcome">Bem-vindo de volta</div>
      <h2>Entrar na plataforma</h2>
      <p>Acesse com seu usuário e senha cadastrados.</p>
    </div>
  </div>
</div>
""")

# Inputs nativos Streamlit (renderizados no fluxo do layout wide)
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

# ─ Feedback de autenticação ─────────────────────────────────────────────────
if btn_entrar:
    if not login_input or not senha_input:
        st.warning("⚠️ Preencha usuário e senha para continuar.")
    else:
        ok, msg = fazer_login(login_input.strip(), senha_input)
        if ok:
            st.switch_page("pages/1_Home.py")
        else:
            st.error(f"❌ {msg}")

if btn_demo:
    st.session_state.update({{
        "autenticado": True, "usuario": "demo", "perfil": "demo",
        "nome": "Visitante", "display_name": "Modo demonstração",
        "email": "", "token": None, "via_api": False,
    }})
    st.switch_page("pages/1_Home.py")

# ─ Rodapé do form ──────────────────────────────────────────────────────────────────
st.html("""
<div class="hip-right-footer">
  HIPNUS COSMÉTICOS &copy; 2026 &mdash; Plataforma exclusiva da marca.<br>
  Acesso restrito a usuários autorizados.
</div>
""")
