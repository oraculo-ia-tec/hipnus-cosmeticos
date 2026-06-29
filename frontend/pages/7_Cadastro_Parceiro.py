"""
7_Cadastro_Parceiro.py — HIPNUS COSMÉTICOS

Página PÚBLICA de cadastro — NEM EXIGE LOGIN.
Acessada pelo convidado via link do e-mail: ?token=<uuid>

Fluxo:
  1. Leitura de ?token= da URL
  2. Validação do token no banco (existe, não expirou, não foi usado)
  3. Pré-preenchimento do e-mail + perfil vindo do token
  4. Formulário de cadastro (nome, senha, cidade, estado)
  5. Criação do usuário e marcação do token como 'usado'

Rota admin (sem token): tab 'Lista de Parceiros' requer login.
"""
from __future__ import annotations
import sys
from pathlib import Path

_ROOT     = Path(__file__).resolve().parents[2]
_FRONTEND = Path(__file__).resolve().parents[1]
for _p in [str(_ROOT), str(_FRONTEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
from lib import ui, components
from lib.user_db import cadastrar_parceiro, listar_parceiros, deletar_parceiro

try:
    from lib.invite_db import validar_invite_db, marcar_invite_usado_db
    _INVITE_DB_OK = True
except ImportError:
    _INVITE_DB_OK = False

st.set_page_config(
    page_title="Cadastro · HIPNUS",
    page_icon="➕",
    layout="centered",
)
ui.inject_theme()

# ─────────────────────────────────────────────────────────────
st.html("""
<style>
[data-testid="stSidebar"] { display: none !important; }
.cad-header {
    text-align: center;
    padding: 28px 0 18px;
}
.cad-logo {
    font-size: 1.05rem; font-weight: 800;
    letter-spacing: 2px; text-transform: uppercase;
    color: #7c3aed; margin-bottom: 4px;
}
.cad-title {
    font-size: 1.6rem; font-weight: 800;
    color: #f5d0fe; line-height: 1.2; margin-bottom: 6px;
}
.cad-sub {
    font-size: .88rem; color: #9ca3af; line-height: 1.5;
}
.cad-card {
    background: #1c1626;
    border: 1px solid rgba(185,131,255,0.22);
    border-radius: 18px;
    padding: 32px 28px;
    margin: 0 auto;
    max-width: 520px;
}
.cad-token-ok {
    background: rgba(16,185,129,.08);
    border: 1px solid rgba(16,185,129,.3);
    border-radius: 10px; padding: 10px 16px;
    color: #10b981; font-size: .82rem; font-weight: 600;
    margin-bottom: 18px;
}
.cad-token-err {
    background: rgba(239,68,68,.08);
    border: 1px solid rgba(239,68,68,.3);
    border-radius: 10px; padding: 10px 16px;
    color: #f87171; font-size: .82rem; font-weight: 600;
    margin-bottom: 18px;
}
.cad-perfil-badge {
    display: inline-block;
    background: rgba(124,58,237,.18);
    border: 1px solid rgba(168,85,247,.4);
    color: #e879f9; border-radius: 99px;
    padding: 2px 12px; font-size: .75rem; font-weight: 700;
    margin-left: 8px;
}
</style>
""")

# ── Header ────────────────────────────────────────────────────────
st.html("""
<div class="cad-header">
  <div class="cad-logo">💫 HIPNUS COSMÉTICOS</div>
  <div class="cad-title">Criar minha conta</div>
  <div class="cad-sub">Preencha os dados abaixo para ativar seu acesso.</div>
</div>
""")

# ── Ler token da URL ────────────────────────────────────────────────────
params = st.query_params
token  = params.get("token", "").strip()

_email_pre  = ""
_role_pre   = "b2b"
_token_valido = False
_token_msg    = ""
_invite_data  = {}

if token:
    if not _INVITE_DB_OK:
        _token_msg = "⚠️ Módulo invite_db não encontrado. Cadastro manual liberado."
        _token_valido = True
    else:
        try:
            _invite_data = validar_invite_db(token) or {}
            if _invite_data:
                _email_pre    = _invite_data.get("email", "")
                _role_pre     = _invite_data.get("role",  "b2b")
                _token_valido = True
                _token_msg    = f"✅ Convite válido para {_email_pre}"
            else:
                _token_msg = "❌ Token inválido, expirado ou já utilizado."
        except Exception as _e:
            _token_msg = f"⚠️ Não foi possível validar o token: {_e}. Prossiga mesmo assim."
            _token_valido = True
else:
    _token_msg = ""

ROLE_LABELS = {
    "b2b":   "💇 Parceiro / Salão B2B",
    "b2c":   "👤 Cliente Final B2C",
    "admin": "🛡️ Administrador",
}

# ── Formulário de cadastro ──────────────────────────────────────────────
if token and _token_msg:
    if _token_valido:
        st.html(f'<div class="cad-token-ok">{_token_msg}</div>')
    else:
        st.html(f'<div class="cad-token-err">{_token_msg}</div>')
        st.info("🔐 Solicite um novo convite ao administrador.")
        st.stop()

if not token:
    # Acesso sem token — formulário simples sem pré-preenchimento
    st.info("🔗 Acesso direto. Se você recebeu um convite, use o link do e-mail para pré-preencher seus dados.")

with st.form("form_cadastro_publico", clear_on_submit=True):
    nome  = st.text_input("👤 Nome completo", placeholder="Ex: Joana Silva")
    email = st.text_input(
        "📧 E-mail",
        value=_email_pre,
        disabled=bool(_email_pre),        # bloqueia edição se veio do token
        placeholder="seuemail@email.com",
    )
    senha  = st.text_input("🔒 Crie uma senha", type="password", placeholder="Mínimo 6 caracteres")
    senha2 = st.text_input("🔒 Confirme a senha", type="password", placeholder="Repita a senha")

    col_c, col_e = st.columns(2)
    with col_c:
        cidade = st.text_input("📍 Cidade", placeholder="Ex: São Paulo")
    with col_e:
        estado = st.text_input("🇺🏳️ Estado (UF)", placeholder="Ex: SP", max_chars=2)

    # Perfil: pré-definido pelo token (read-only via caption) ou selecionável
    if _email_pre and _role_pre:
        perfil = _role_pre
        st.html(
            f'<div style="margin:4px 0 8px;font-size:.82rem;color:#9ca3af;">'
            f'Perfil do convite: <span class="cad-perfil-badge">{ROLE_LABELS.get(perfil, perfil)}</span>'
            f'</div>'
        )
    else:
        perfil = st.selectbox("🏠 Perfil de acesso", ["b2b", "b2c"],
                              format_func=lambda v: ROLE_LABELS.get(v, v))

    submit = st.form_submit_button(
        "✅ Criar minha conta",
        use_container_width=True,
        type="primary",
    )

if submit:
    _erros = []
    if not nome.strip():               _erros.append("Nome obrigatório.")
    if not email.strip() or "@" not in email: _erros.append("E-mail inválido.")
    if len(senha) < 6:                 _erros.append("Senha deve ter ao menos 6 caracteres.")
    if senha != senha2:                _erros.append("As senhas não coincidem.")

    if _erros:
        for e in _erros:
            st.error(e)
    else:
        try:
            cadastrar_parceiro(
                nome=nome.strip(),
                email=email.strip(),
                senha=senha,
                perfil=perfil,
                cidade=cidade.strip(),
                estado=estado.upper().strip(),
            )
            # Marca token como usado
            if token and _INVITE_DB_OK and _token_valido and _invite_data:
                try:
                    marcar_invite_usado_db(token)
                except Exception:
                    pass

            st.success("🎉 Conta criada com sucesso!")
            st.balloons()
            st.info("🔐 Agora faça login para acessar a plataforma HIPNUS.")
            st.page_link("app.py", label="→ Ir para o Login", icon="🔐")
        except Exception as exc:
            msg = str(exc)
            if "já cadastrado" in msg.lower() or "unique" in msg.lower() or "already exists" in msg.lower():
                st.warning("⚠️ Este e-mail já possui cadastro. Faça login ou use 'Esqueci minha senha'.")
            else:
                st.error(f"Erro ao criar conta: {exc}")

st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#6b7280;font-size:.78rem;'>HIPNUS COSMÉTICOS &copy; 2026</div>",
    unsafe_allow_html=True,
)
