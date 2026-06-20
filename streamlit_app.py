"""
streamlit_app.py — HIPNUS COSMÉTICOS
======================================
Entrypoint do Streamlit Cloud — página de Login.

Estratégia de layout:
  Todo o HTML (painel esquerdo + painel direito com formulário) é renderizado
  dentro de um único st.html() para que o CSS posicione os dois painéis
  lado a lado sem interferência do grid do Streamlit.

  O submit do formulário usa window.location para passar as credenciais via
  query_params. O Streamlit lê st.query_params['_u'] e st.query_params['_p']
  e chama fazer_login() normalmente.

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
from lib.auth import fazer_login
from lib.theme import inject_theme, inject_login_style

# ─ Configuração da página ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="Login — HIPNUS COSMÉTICOS",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_theme()
inject_login_style()

# ─ Redireciona se já autenticado ─────────────────────────────────────────────
if st.session_state.get("autenticado"):
    st.switch_page("pages/1_Home.py")

# ─ Lê credenciais enviadas via query_params (submit do form HTML) ─────────────
qp = st.query_params
_login_qp = qp.get("_u", "").strip()
_senha_qp  = qp.get("_p", "").strip()
_demo_qp   = qp.get("_demo", "")

if _demo_qp == "1":
    st.query_params.clear()
    st.session_state.update({
        "autenticado": True, "usuario": "demo", "perfil": "demo",
        "nome": "Visitante", "display_name": "Modo demonstração",
        "email": "", "token": None, "via_api": False,
    })
    st.switch_page("pages/1_Home.py")

_erro_msg = ""
if _login_qp and _senha_qp:
    ok, msg = fazer_login(_login_qp, _senha_qp)
    st.query_params.clear()
    if ok:
        st.switch_page("pages/1_Home.py")
    else:
        _erro_msg = msg
elif _login_qp and not _senha_qp:
    st.query_params.clear()
    _erro_msg = "Preencha a senha para continuar."

# ─ Renderiza toda a página de login como HTML único ───────────────────────────
st.html(f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
/* ── Reset Streamlit ────────────────────────────────────────────────────── */
[data-testid="stMainBlockContainer"],
[data-testid="stMain"] > div,
.block-container {{
  padding: 0 !important;
  max-width: 100% !important;
  margin: 0 !important;
}}
[data-testid="stToolbar"],
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
header[data-testid="stHeader"] {{
  display: none !important;
}}

/* ── Layout split-screen ───────────────────────────────────────────────── */
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: 'Inter', system-ui, sans-serif; }}

.hip-login-wrap {{
  display: flex;
  min-height: 100vh;
  width: 100%;
}}

/* ─── PAINEL ESQUERDO ──────────────────────────────────────────────────── */
.hip-panel-left {{
  flex: 1 1 55%;
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
.hip-panel-left::before {{
  content: "";
  position: absolute; top: -120px; right: -120px;
  width: 420px; height: 420px; border-radius: 50%;
  background: rgba(255,255,255,0.04); pointer-events: none;
}}
.hip-panel-left::after {{
  content: "";
  position: absolute; bottom: -80px; left: -80px;
  width: 300px; height: 300px; border-radius: 50%;
  background: rgba(255,255,255,0.03); pointer-events: none;
}}

/* Logo */
.hip-left-logo {{
  display: flex; align-items: center; gap: 14px;
  animation: fadeSlideRight 0.6s 0.1s cubic-bezier(0.16,1,0.3,1) both;
}}
.hip-left-logo-icon {{
  width: 48px; height: 48px; border-radius: 14px;
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.25);
  display: flex; align-items: center; justify-content: center;
  font-weight: 900; font-size: 1.4rem; color: #fff; letter-spacing: -1px;
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

/* Hero */
.hip-left-hero {{
  padding: 0 0 16px;
  animation: fadeSlideRight 0.6s 0.2s cubic-bezier(0.16,1,0.3,1) both;
}}
.hip-left-hero .kicker {{
  display: inline-block;
  background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.2);
  color: rgba(255,255,255,.85);
  font-size: .66rem; font-weight: 700; letter-spacing: 2px;
  text-transform: uppercase; padding: 5px 14px; border-radius: 999px;
  margin-bottom: 22px;
}}
.hip-left-hero h1 {{
  font-size: clamp(1.8rem, 3vw, 2.8rem); font-weight: 800;
  color: #fff; line-height: 1.2; letter-spacing: -.5px; margin: 0 0 18px;
}}
.hip-left-hero h1 span {{
  background: linear-gradient(90deg, #e2b4ff, #b983ff);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}}
.hip-left-hero p {{
  color: rgba(255,255,255,.7); font-size: .95rem;
  line-height: 1.65; max-width: 38ch; margin: 0 0 32px;
}}

/* Claims */
.hip-left-claims {{ display: flex; flex-direction: column; gap: 14px; }}
.hip-left-claim {{ display: flex; align-items: center; gap: 12px; }}
.hip-left-claim .claim-icon {{
  width: 34px; height: 34px; border-radius: 10px;
  background: rgba(255,255,255,.1); border: 1px solid rgba(255,255,255,.18);
  display: flex; align-items: center; justify-content: center;
  font-size: 1rem; flex-shrink: 0;
}}
.hip-left-claim .claim-text {{
  font-size: .85rem; color: rgba(255,255,255,.8);
  font-weight: 500; line-height: 1.35;
}}
.hip-left-claim .claim-text strong {{
  color: #fff; font-weight: 700; display: block; font-size: .88rem;
}}

/* Footer esquerdo */
.hip-left-footer {{
  font-size: .68rem; color: rgba(255,255,255,.35); letter-spacing: .5px;
}}

/* ─── PAINEL DIREITO ──────────────────────────────────────────────────── */
.hip-panel-right {{
  flex: 0 0 420px;
  background: #f8f7fc;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 32px;
  animation: fadeSlideLeft 0.7s cubic-bezier(0.16,1,0.3,1) both;
}}

.hip-form-wrap {{
  width: 100%;
  max-width: 360px;
}}

/* Header do form */
.hip-form-header {{ margin-bottom: 28px; }}
.hip-form-header .welcome {{
  font-size: .72rem; font-weight: 700;
  color: #7c3aed; letter-spacing: 1.5px; text-transform: uppercase;
  margin-bottom: 8px;
  display: flex; align-items: center; gap: 8px;
}}
.hip-form-header .welcome::before {{
  content: ""; display: inline-block;
  width: 18px; height: 2px; background: #7c3aed; border-radius: 1px;
}}
.hip-form-header h2 {{
  font-size: 1.55rem; font-weight: 800;
  color: #1a0a2e; letter-spacing: -.5px; line-height: 1.2; margin: 0 0 7px;
}}
.hip-form-header p {{
  font-size: .85rem; color: #6b7280; line-height: 1.5; margin: 0;
}}

/* Inputs */
.hip-field {{ margin-bottom: 16px; }}
.hip-field label {{
  display: block; font-size: .78rem; font-weight: 600;
  color: #4b4567; letter-spacing: .2px; margin-bottom: 7px;
}}
.hip-field input {{
  width: 100%;
  background: #fff;
  border: 1.5px solid #e5e0f5;
  border-radius: 12px;
  font-size: .97rem;
  padding: 13px 16px;
  color: #1a0a2e;
  outline: none;
  transition: border-color .18s, box-shadow .18s;
  font-family: inherit;
}}
.hip-field input::placeholder {{ color: #c4bfd8; }}
.hip-field input:focus {{
  border-color: #7c3aed;
  box-shadow: 0 0 0 4px rgba(124,58,237,.12);
}}

/* Erro */
.hip-error {{
  background: #fdf2f8; border: 1px solid #f0c4df;
  border-radius: 10px; padding: 11px 14px;
  font-size: .83rem; color: #9b2777;
  margin-bottom: 16px;
  display: {'flex' if _erro_msg else 'none'};
  align-items: center; gap: 8px;
}}

/* Botões */
.hip-btn-primary {{
  width: 100%;
  background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%);
  border: none; border-radius: 12px;
  height: 50px;
  font-size: .97rem; font-weight: 700; letter-spacing: .3px;
  color: #fff; cursor: pointer;
  box-shadow: 0 4px 20px rgba(124,58,237,.35);
  transition: all .18s cubic-bezier(0.16,1,0.3,1);
  font-family: inherit;
  margin-bottom: 10px;
}}
.hip-btn-primary:hover {{
  box-shadow: 0 8px 28px rgba(124,58,237,.45);
  transform: translateY(-1px);
}}
.hip-btn-primary:active {{ transform: translateY(0); }}

.hip-btn-demo {{
  width: 100%;
  background: #fff;
  border: 1.5px solid #e5e0f5;
  border-radius: 12px; height: 46px;
  font-size: .87rem; font-weight: 600;
  color: #7c3aed; cursor: pointer;
  transition: all .18s ease;
  font-family: inherit;
}}
.hip-btn-demo:hover {{
  background: #f3f0ff; border-color: #7c3aed;
}}

/* Divisor */
.hip-divider {{
  display: flex; align-items: center; gap: 10px;
  margin: 12px 0; color: #c4bfd8; font-size: .75rem;
}}
.hip-divider::before, .hip-divider::after {{
  content: ""; flex: 1; height: 1px; background: #ede9f8;
}}

/* Footer form */
.hip-form-footer {{
  text-align: center; margin-top: 24px;
  font-size: .7rem; color: #b0a9c8; line-height: 1.7;
}}

/* ── Animações ───────────────────────────────────────────────────────── */
@keyframes fadeSlideRight {{
  from {{ opacity: 0; transform: translateX(-24px); }}
  to   {{ opacity: 1; transform: translateX(0); }}
}}
@keyframes fadeSlideLeft {{
  from {{ opacity: 0; transform: translateX(24px); }}
  to   {{ opacity: 1; transform: translateX(0); }}
}}

/* ── Responsivo ──────────────────────────────────────────────────────── */
@media (max-width: 860px) {{
  .hip-panel-left {{ display: none; }}
  .hip-panel-right {{
    flex: 1; padding: 40px 20px;
  }}
}}
</style>
</head>
<body>
<div class="hip-login-wrap">

  <!-- PAINEL ESQUERDO -->
  <div class="hip-panel-left">
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

  <!-- PAINEL DIREITO -->
  <div class="hip-panel-right">
    <div class="hip-form-wrap">

      <div class="hip-form-header">
        <div class="welcome">Bem-vindo de volta</div>
        <h2>Entrar na plataforma</h2>
        <p>Acesse com seu usuário e senha cadastrados.</p>
      </div>

      <!-- Mensagem de erro (visível só se houver erro) -->
      <div class="hip-error" id="hip-error">
        ❌ {_erro_msg}
      </div>

      <form id="hip-login-form">
        <div class="hip-field">
          <label for="hip-usuario">Usuário</label>
          <input
            type="text"
            id="hip-usuario"
            name="usuario"
            placeholder="seu.usuario"
            autocomplete="username"
            required
          />
        </div>

        <div class="hip-field">
          <label for="hip-senha">Senha</label>
          <input
            type="password"
            id="hip-senha"
            name="senha"
            placeholder="••••••••"
            autocomplete="current-password"
            required
          />
        </div>

        <button type="submit" class="hip-btn-primary">
          Entrar &nbsp;→
        </button>
      </form>

      <div class="hip-divider">ou</div>

      <button class="hip-btn-demo" onclick="acessarDemo()">
        Acessar modo demonstração
      </button>

      <div class="hip-form-footer">
        HIPNUS COSMÉTICOS &copy; 2026<br>
        Plataforma exclusiva da marca. Acesso restrito.
      </div>
    </div>
  </div>

</div>

<script>
  // Submit do formulário → passa credenciais via query_params ao Streamlit
  document.getElementById('hip-login-form').addEventListener('submit', function(e) {{
    e.preventDefault();
    var u = document.getElementById('hip-usuario').value.trim();
    var p = document.getElementById('hip-senha').value;
    if (!u || !p) return;
    var url = window.location.href.split('?')[0];
    window.parent.location.href = url + '?_u=' + encodeURIComponent(u) + '&_p=' + encodeURIComponent(p);
  }});

  function acessarDemo() {{
    var url = window.location.href.split('?')[0];
    window.parent.location.href = url + '?_demo=1';
  }}
</script>
</body>
</html>
""")
