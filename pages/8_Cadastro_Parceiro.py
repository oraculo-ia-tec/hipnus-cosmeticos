"""
pages/8_Cadastro_Parceiro.py — HIPNUS COSMÉTICOS

Página PÚBLICA de cadastro via convite.
Acessada pelo convidado com: ?token=<uuid>

Fluxo:
  1. Lê ?token= da URL
  2. Valida token no banco (existe / não expirado / não usado)
  3. Pré-preenche e-mail + perfil vindos do token
  4. Formulário (nome, senha, cidade, estado)
  5. Cria conta e marca token como 'usado'
"""
from __future__ import annotations
import sys
from pathlib import Path

_ROOT     = Path(__file__).resolve().parents[1]
_FRONTEND = _ROOT / "frontend"
for _p in [str(_ROOT), str(_FRONTEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
from lib import ui

try:
    from lib.user_db import cadastrar_parceiro
except ImportError:
    cadastrar_parceiro = None

try:
    from lib.invite_db import validar_invite_db, marcar_invite_usado_db
    _INVITE_DB_OK = True
except ImportError:
    _INVITE_DB_OK = False

st.set_page_config(
    page_title="Criar conta · HIPNUS",
    page_icon="⭐",
    layout="centered",
    initial_sidebar_state="collapsed",
)
ui.inject_theme()

# Esconde sidebar completamente — página pública
st.html("""
<style>
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
header[data-testid="stHeader"] { display: none !important; }

.cad-wrap {
  max-width: 480px; margin: 40px auto 0;
}
.cad-logo {
  text-align: center; margin-bottom: 28px;
}
.cad-logo-icon {
  display: inline-flex; align-items: center; justify-content: center;
  width: 56px; height: 56px; border-radius: 18px;
  background: linear-gradient(135deg,#7c3aed,#5b21b6);
  font-family: 'Playfair Display',serif;
  font-size: 1.6rem; font-weight: 900; color: #fff;
  box-shadow: 0 8px 28px rgba(124,58,237,0.4);
  margin: 0 auto 12px;
}
.cad-logo-name {
  font-family: 'Playfair Display',serif;
  font-size: 1.1rem; font-weight: 800;
  color: #1a0a2e; letter-spacing: -.3px;
}
.cad-logo-sub {
  font-size: .65rem; color: #9ca3af;
  letter-spacing: 2.5px; text-transform: uppercase; margin-top: 2px;
}
.cad-title {
  text-align: center; margin-bottom: 28px;
}
.cad-title h2 {
  font-family: 'Playfair Display',serif;
  font-size: 1.55rem; font-weight: 800;
  color: #1a0a2e; margin: 0 0 6px;
}
.cad-title p {
  font-size: .85rem; color: #6b7280; margin: 0;
}
.token-ok {
  background: #ecfdf5; border: 1px solid #a7f3d0;
  border-radius: 10px; padding: 10px 16px;
  color: #065f46; font-size: .82rem; font-weight: 600;
  margin-bottom: 18px;
}
.token-err {
  background: #fef2f2; border: 1px solid #fecaca;
  border-radius: 10px; padding: 10px 16px;
  color: #991b1b; font-size: .82rem; font-weight: 600;
  margin-bottom: 18px;
}
.perfil-badge {
  background: #f3e8ff; border: 1px solid #d8b4fe;
  color: #7c3aed; border-radius: 99px;
  padding: 2px 12px; font-size: .72rem; font-weight: 700;
  display: inline-block; margin-left: 6px;
}
</style>
""")

ROLE_LABELS = {
    "b2b":   "💇 Parceiro / Salão B2B",
    "b2c":   "👤 Cliente Final B2C",
    "admin": "🛡️ Administrador",
}

# ─── Leitura e validação do token ─────────────────────────────────────────
params = st.query_params
token  = params.get("token", "").strip()

_email_pre    = ""
_role_pre     = "b2b"
_token_valido = False
_token_msg    = ""
_invite_data  = {}

if token:
    if not _INVITE_DB_OK:
        _token_msg    = "⚠️ Módulo de convites indisponível. Preencha manualmente."
        _token_valido = True
    else:
        try:
            _invite_data = validar_invite_db(token) or {}
            if _invite_data:
                _email_pre    = _invite_data.get("email", "")
                _role_pre     = _invite_data.get("role", "b2b")
                _token_valido = True
                _token_msg    = f"✅ Convite válido · {_email_pre}"
            else:
                _token_msg = "❌ Convite inválido, expirado ou já utilizado."
        except Exception as _e:
            _token_msg    = f"⚠️ Não foi possível validar o convite: {_e}. Preencha manualmente."
            _token_valido = True

# ─── Cabeçalho visual ───────────────────────────────────────────────────────
st.html("""
<div class="cad-wrap">
  <div class="cad-logo">
    <div class="cad-logo-icon">H</div>
    <div class="cad-logo-name">HIPNUS</div>
    <div class="cad-logo-sub">Cosméticos</div>
  </div>
  <div class="cad-title">
    <h2>Criar minha conta</h2>
    <p>Preencha os dados abaixo para ativar seu acesso.</p>
  </div>
</div>
""")

# ─── Exibe status do token ─────────────────────────────────────────────────
if token:
    if _token_valido:
        st.html(f'<div class="token-ok">{_token_msg}</div>')
    else:
        st.html(f'<div class="token-err">{_token_msg}</div>')
        st.info("🔐 Solicite um novo convite ao administrador.")
        st.stop()
else:
    st.info("🔗 Acesso direto. Se você recebeu um convite, use o link do e-mail para pré-preencher seus dados.")

# ─── Formulário ────────────────────────────────────────────────────────────
with st.form("form_cadastro", clear_on_submit=True):
    nome  = st.text_input("👤 Nome completo", placeholder="Ex: Joana Silva")
    email = st.text_input(
        "📧 E-mail",
        value=_email_pre,
        disabled=bool(_email_pre),
        placeholder="seuemail@email.com",
    )
    senha  = st.text_input("🔒 Crie uma senha", type="password", placeholder="Mínimo 6 caracteres")
    senha2 = st.text_input("🔒 Confirme a senha", type="password", placeholder="Repita a senha")

    col_c, col_e = st.columns(2)
    with col_c:
        cidade = st.text_input("📍 Cidade")
    with col_e:
        estado = st.text_input("🇺🏳️ Estado (UF)", max_chars=2)

    if _email_pre:
        perfil = _role_pre
        st.html(
            f'<div style="font-size:.82rem;color:#6b7280;margin:4px 0 8px;">'
            f'Perfil do convite: <span class="perfil-badge">{ROLE_LABELS.get(perfil, perfil)}</span>'
            f'</div>'
        )
    else:
        perfil = st.selectbox(
            "🏠 Perfil",
            ["b2b", "b2c"],
            format_func=lambda v: ROLE_LABELS.get(v, v),
        )

    submit = st.form_submit_button(
        "✅ Criar minha conta",
        use_container_width=True,
        type="primary",
    )

if submit:
    erros = []
    if not nome.strip():                     erros.append("Nome obrigatório.")
    if not email.strip() or "@" not in email: erros.append("E-mail inválido.")
    if len(senha) < 6:                       erros.append("Senha deve ter ao menos 6 caracteres.")
    if senha != senha2:                      erros.append("As senhas não coincidem.")

    if erros:
        for e in erros:
            st.error(e)
    elif cadastrar_parceiro is None:
        st.error("❌ Módulo de cadastro não disponível. Contate o administrador.")
    else:
        try:
            cadastrar_parceiro(
                nome=nome.strip(), email=email.strip(), senha=senha,
                perfil=perfil, cidade=cidade.strip(), estado=estado.upper().strip(),
            )
            if token and _INVITE_DB_OK and _token_valido and _invite_data:
                try:
                    marcar_invite_usado_db(token)
                except Exception:
                    pass

            st.success("🎉 Conta criada com sucesso!")
            st.balloons()
            st.info("🔐 Agora faça login para acessar a plataforma HIPNUS.")
            st.markdown(
                "**[\u2192 Ir para o Login](/)** ",
                unsafe_allow_html=True,
            )
        except Exception as exc:
            msg = str(exc)
            if any(k in msg.lower() for k in ["já cadastrado", "unique", "already exists", "duplicate"]):
                st.warning("⚠️ Este e-mail já possui cadastro. Faça login ou recupere sua senha.")
            else:
                st.error(f"Erro ao criar conta: {exc}")

st.markdown(
    "<hr><div style='text-align:center;color:#9ca3af;font-size:.75rem;'>"
    "HIPNUS COSMÉTICOS &copy; 2026</div>",
    unsafe_allow_html=True,
)
