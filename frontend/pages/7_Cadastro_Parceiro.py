"""
7_Cadastro_Parceiro.py — HIPNUS COSMÉTICOS
============================================
Página PÚblica de cadastro via convite.

Acesso:
  Convidado clica no link recebido por e-mail:
    https://hipnus-cosmeticos.streamlit.app/Cadastro_Parceiro?token=<token>

Fluxo corrigido (v8):
  1. Página é PÚblica — não exige login (sem require_auth).
  2. Lê ?token= dos query params imediatamente, ANTES de qualquer redirect.
  3. Se não autenticado E há token, preserva o token e exibe o formulário.
  4. Validação: 1º tenta API, 2º valida direto no banco (standalone).
  5. Após cadastro, token é marcado como usado e exibe tela de sucesso.

Bugs corrigidos:
  - Bug #1: require_auth() destruía o ?token= ao redirecionar para login.
  - Bug #2: signup_url apontava para rota errada no Streamlit Cloud.
  - Bug #3: validação db usava import condicional que falha sem FastAPI.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

# ─ Paths ────────────────────────────────────────────────────────────────────────────
_ROOT     = Path(__file__).resolve().parents[2]
_FRONTEND = Path(__file__).resolve().parents[1]
for p in [str(_ROOT), str(_FRONTEND)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from lib.db_utils import resolve_db_url  # noqa: E402
from lib.invite_db import validar_token_db, usar_token_db  # noqa: E402

# ─ Config da página ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cadastro Parceiro | Hipnus Cosméticos",
    page_icon="💼",
    layout="centered",
)

API_URL = st.secrets.get("HIPNUS_API_URL", "http://localhost:8000")


# ─ Helpers ──────────────────────────────────────────────────────────────────────
def validar_email(email: str) -> bool:
    return bool(re.match(r"^[\w.+-]+@[\w-]+\.[\w.]+$", email))


def _validar_token_api(token: str) -> dict | None:
    """Tenta validar token via API FastAPI (opcional, com fallback)."""
    try:
        import requests
        r = requests.get(f"{API_URL}/api/v1/invites/{token}", timeout=4)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def _usar_token_api(token: str, dados: dict) -> tuple[bool, str] | None:
    """Tenta registrar uso do token via API FastAPI (opcional, com fallback)."""
    try:
        import requests
        r = requests.post(f"{API_URL}/api/v1/invites/{token}/use", json=dados, timeout=10)
        if r.status_code in (200, 201):
            return True, "Cadastro realizado com sucesso!"
    except Exception:
        pass
    return None


def validar_token(token: str) -> dict | None:
    """Valida token: 1º API (se disponível), 2º banco direto."""
    resultado = _validar_token_api(token)
    if resultado:
        return resultado
    return validar_token_db(token)


def usar_token(token: str, dados: dict) -> tuple[bool, str]:
    """Marca token como usado: 1º API (se disponível), 2º banco direto."""
    resultado = _usar_token_api(token, dados)
    if resultado:
        return resultado
    return usar_token_db(token, dados)


# ─ Estilos ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.invite-header {
    background: linear-gradient(135deg, #1a0733 0%, #3b1278 40%, #6c2bd9 75%, #8b44f6 100%);
    border-radius: 16px; padding: 2.5rem 2rem 2rem;
    text-align: center; margin-bottom: 2rem; color: white;
}
.invite-header h1 { font-size: 2rem; margin-bottom: .25rem; }
.invite-header p  { opacity: .8; font-size: 1rem; margin: 0; }
.success-box {
    background: #d4edda; border: 1px solid #c3e6cb; border-radius: 12px;
    padding: 1.5rem; text-align: center; color: #155724;
}
</style>
""", unsafe_allow_html=True)


# ─ Cabeçalho ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="invite-header">
    <h1>💼 Hipnus Cosméticos</h1>
    <p>Você foi convidado para se tornar um parceiro</p>
</div>
""", unsafe_allow_html=True)


# ─ Inicializa sessão ────────────────────────────────────────────────────────────
for key, default in [
    ("cadastro_ok",    False),
    ("invite_data",    None),
    ("token_validado", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ─ Tela de sucesso (após cadastro concluído) ──────────────────────────────────
if st.session_state.cadastro_ok:
    st.markdown("""
    <div class="success-box">
        <h2>✅ Cadastro realizado!</h2>
        <p>Bem-vindo à família Hipnus Cosméticos.<br>
        Aguarde o contato da nossa equipe para ativar sua conta.</p>
    </div>
    """, unsafe_allow_html=True)
    st.balloons()
    if st.button("🏠 Ir para a Home", use_container_width=True):
        st.switch_page("streamlit_app.py")
    st.stop()


# ─ Lê token dos query params (ANTES de qualquer redirect) ────────────────────
# IMPORTANTE: esta página é PÚblica — não usa require_auth().
# O convidado ainda não tem cadastro nem login.
token = st.query_params.get("token", "").strip()

if not token:
    st.info("ℹ️ Acesse esta página pelo link do seu convite, ou cole o código abaixo.")
    token_input = st.text_input("Código do convite", placeholder="cole aqui o token")
    if token_input:
        token = token_input.strip()

if not token:
    st.stop()


# ─ Validação do token ──────────────────────────────────────────────────────────
if st.session_state.token_validado != token:
    with st.spinner("Validando seu convite..."):
        invite = validar_token(token)
    if invite is None:
        st.error(
            "❌ Convite inválido, expirado ou já utilizado. "
            "Solicite um novo convite ao administrador."
        )
        with st.expander("🔧 Detalhes técnicos (admin)"):
            st.code(
                f"API_URL:      {API_URL}\n"
                f"DATABASE_URL: {resolve_db_url()}\n"
                f"Token:        {token[:16]}...",
                language="text",
            )
        st.stop()
    st.session_state.invite_data    = invite
    st.session_state.token_validado = token

invite = st.session_state.invite_data


# ─ Exibe dados do convite válido ─────────────────────────────────────────────────
role_labels = {
    "distribuidor": "🏗️ Distribuidor",
    "revendedor":   "🛍️ Revendedor",
    "salao":        "✂️ Salão",
    "profissional": "💇 Profissional",
    "parceiro":     "🤝 Parceiro",
    "b2b":          "🎤 Profissional / Salão",
    "b2c":          "👤 Cliente Final",
    "admin":        "🛡️ Administrador",
}
role       = invite.get("role", "parceiro")
role_label = role_labels.get(role, role.capitalize())
try:
    exp_str = datetime.fromisoformat(invite.get("expires_at", "")).strftime("%d/%m/%Y às %H:%M")
except Exception:
    exp_str = invite.get("expires_at", "—")

st.success(f"✅ Convite válido! Perfil: **{role_label}** — expira em {exp_str}")
st.subheader("Preencha seus dados")


# ─ Formulário de cadastro ────────────────────────────────────────────────────────
with st.form("form_cadastro_parceiro", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1:
        nome     = st.text_input("Nome completo *",         placeholder="João da Silva")
        email    = st.text_input(
            "E-mail *",
            value=invite.get("email", ""),
            disabled=bool(invite.get("email")),
        )
        telefone = st.text_input("Telefone / WhatsApp *",   placeholder="(31) 99999-9999")
    with col2:
        empresa = st.text_input("Nome do negócio",          placeholder="Salão Beleza Total")
        cidade  = st.text_input("Cidade *",                 placeholder="Belo Horizonte")
        estado  = st.selectbox("Estado *", [
            "MG","SP","RJ","ES","BA","GO","DF","PR","SC","RS",
            "MT","MS","AM","PA","CE","PE","MA","PB","RN","AL",
            "SE","PI","TO","RO","AC","RR","AP",
        ])
    senha  = st.text_input("Crie uma senha *", type="password", placeholder="mínimo 8 caracteres")
    senha2 = st.text_input("Confirme a senha *", type="password")
    aceite = st.checkbox(
        "Li e aceito os termos de uso e política de privacidade da Hipnus Cosméticos"
    )
    submitted = st.form_submit_button(
        "✅ Concluir cadastro",
        use_container_width=True,
        type="primary",
    )


# ─ Processamento do cadastro ────────────────────────────────────────────────────
if submitted:
    erros = []
    if not nome.strip():            erros.append("Nome é obrigatório.")
    if not email.strip():           erros.append("E-mail é obrigatório.")
    elif not validar_email(email):  erros.append("E-mail inválido.")
    if not telefone.strip():        erros.append("Telefone é obrigatório.")
    if not cidade.strip():          erros.append("Cidade é obrigatória.")
    if len(senha) < 8:              erros.append("Senha deve ter ao menos 8 caracteres.")
    if senha != senha2:             erros.append("As senhas não coincidem.")
    if not aceite:                  erros.append("Você precisa aceitar os termos de uso.")

    if erros:
        for e in erros:
            st.error(e)
    else:
        payload = {
            "nome":     nome.strip(),
            "email":    email.strip(),
            "telefone": telefone.strip(),
            "empresa":  empresa.strip(),
            "cidade":   cidade.strip(),
            "estado":   estado,
            "senha":    senha,
            "role":     role,
            "token":    token,
        }
        ok, msg = usar_token(token, payload)
        if ok:
            st.session_state.cadastro_ok = True
            st.rerun()
        else:
            st.error(f"❌ {msg}")
