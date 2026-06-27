"""
7_Cadastro_Parceiro.py — HIPNUS COSMÉTICOS
============================================
Página acessada pelo convidado através do link personalizado.

Fluxo de validação (com fallback):
  1. Lê ?token= da query string
  2a. Tenta validar via API (GET /api/v1/invites/{token})
  2b. Fallback: valida diretamente no banco SQLAlchemy
  3. Exibe formulário pré-preenchido
  4. Ao submeter:
     4a. Tenta POST /api/v1/invites/{token}/use
     4b. Fallback: marca como usado no banco diretamente
  5. Sucesso

Configuração esperada em .streamlit/secrets.toml:
  DATABASE_URL = "sqlite:///./data/hipnus.db"
  APP_BASE_URL = "https://hipnus-cosmeticos.streamlit.app"
"""
from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import streamlit as st

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ─── Config ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cadastro Parceiro | Hipnus Cosméticos",
    page_icon="💼",
    layout="centered",
)

API_URL = st.secrets.get("HIPNUS_API_URL", "http://localhost:8000")


# ─── Resolve DATABASE_URL (secrets > environ > default) ───────────────────────────
def _resolve_db_url() -> str:
    try:
        val = st.secrets.get("DATABASE_URL")
        if val: return val.strip().strip('"').strip("'")
    except Exception:
        pass
    try:
        val = st.secrets["default"].get("DATABASE_URL")
        if val: return val.strip().strip('"').strip("'")
    except Exception:
        pass
    val = os.environ.get("DATABASE_URL")
    if val: return val
    return "sqlite:///./data/hipnus.db"


# ─── Fallback: acesso direto ao banco ───────────────────────────────────────────────

def _get_db_session():
    """Abre sessão SQLAlchemy com DATABASE_URL resolvido dos secrets."""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        db_url = _resolve_db_url()
        if db_url.startswith("sqlite:///"):
            db_path = Path(db_url.replace("sqlite:///", "", 1))
            db_path.parent.mkdir(parents=True, exist_ok=True)
        connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
        engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
        # Garante tabelas
        from app.db.base import Base
        import app.domains.invites.models  # noqa: F401
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        return Session(), None
    except Exception as exc:
        return None, str(exc)


def _validar_token_db(token: str) -> dict | None:
    db, err = _get_db_session()
    if not db:
        return None
    try:
        from app.domains.invites.models import Invite
        invite = db.query(Invite).filter(Invite.token == token).first()
        if not invite or invite.used:
            return None
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if invite.expires_at < now:
            return None
        return {
            "id": invite.id, "token": invite.token, "email": invite.email,
            "role": invite.role, "created_by": invite.created_by, "used": invite.used,
            "expires_at": invite.expires_at.isoformat(),
            "created_at": invite.created_at.isoformat() if invite.created_at else "",
        }
    except Exception:
        return None
    finally:
        db.close()


def _usar_token_db(token: str, dados: dict) -> tuple[bool, str]:
    db, err = _get_db_session()
    if not db:
        return False, f"Banco indisponível: {err}"
    try:
        from app.domains.invites.models import Invite
        invite = db.query(Invite).filter(Invite.token == token).first()
        if not invite:
            return False, "Token não encontrado."
        invite.used    = True
        invite.used_at = datetime.now(timezone.utc)
        db.commit()
        return True, "Cadastro realizado com sucesso!"
    except Exception as exc:
        db.rollback()
        return False, str(exc)
    finally:
        db.close()


# ─── Helpers via API (com fallback no banco) ─────────────────────────────────────────

def validar_token(token: str) -> dict | None:
    try:
        r = requests.get(f"{API_URL}/api/v1/invites/{token}", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return _validar_token_db(token)


def usar_token(token: str, dados: dict) -> tuple[bool, str]:
    try:
        r = requests.post(f"{API_URL}/api/v1/invites/{token}/use", json=dados, timeout=10)
        if r.status_code in (200, 201):
            return True, "Cadastro realizado com sucesso!"
    except Exception:
        pass
    return _usar_token_db(token, dados)


def validar_email(email: str) -> bool:
    return bool(re.match(r"^[\w.+-]+@[\w-]+\.[\w.]+$", email))


# ─── Estilos ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.invite-header {
    background: linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);
    border-radius:16px;padding:2.5rem 2rem 2rem;
    text-align:center;margin-bottom:2rem;color:white;
}
.invite-header h1 { font-size:2rem;margin-bottom:.25rem; }
.invite-header p  { opacity:.8;font-size:1rem;margin:0; }
.success-box {
    background:#d4edda;border:1px solid #c3e6cb;border-radius:12px;
    padding:1.5rem;text-align:center;color:#155724;
}
</style>
""", unsafe_allow_html=True)

# ─── Lógica principal ──────────────────────────────────────────────────────────────────

token_url = st.query_params.get("token")

st.markdown("""
<div class="invite-header">
    <h1>💼 Hipnus Cosméticos</h1>
    <p>Você foi convidado para se tornar um parceiro</p>
</div>
""", unsafe_allow_html=True)

for key, default in [("cadastro_ok", False), ("invite_data", None), ("token_validado", None)]:
    if key not in st.session_state:
        st.session_state[key] = default

if st.session_state.cadastro_ok:
    st.markdown("""
    <div class="success-box">
        <h2>✅ Cadastro realizado!</h2>
        <p>Bem-vindo à família Hipnus Cosméticos.<br>
        Em breve você receberá um e-mail de confirmação.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🏠 Ir para a Home", use_container_width=True):
        st.switch_page("pages/1_Home.py")
    st.stop()

token = token_url
if not token:
    st.info("ℹ️ Acesse esta página pelo link do seu convite, ou cole o código abaixo.")
    token_input = st.text_input("Código do convite", placeholder="cole aqui o token do seu convite")
    if token_input:
        token = token_input.strip()

if not token:
    st.info("Aguardando código de convite...")
    st.stop()

# Validação do token
if st.session_state.token_validado != token:
    with st.spinner("Validando seu convite..."):
        invite = validar_token(token)
    if invite is None:
        st.error("❌ Convite inválido, expirado ou já utilizado. Solicite um novo convite ao administrador.")
        db_url = _resolve_db_url()
        with st.expander("🔧 Detalhes técnicos (admin)"):
            st.code(
                f"API_URL:      {API_URL}\n"
                f"DATABASE_URL: {db_url}\n"
                f"Token:        {token[:16]}...",
                language="text",
            )
        st.stop()
    st.session_state.invite_data    = invite
    st.session_state.token_validado = token

invite = st.session_state.invite_data

role_labels = {
    "distribuidor": "🏗️ Distribuidor", "revendedor": "🛍️ Revendedor",
    "salao": "✂️ Salão de Beleza", "profissional": "💇 Profissional",
    "parceiro": "🤝 Parceiro", "b2b": "🎤 Profissional / Salão",
    "b2c": "👤 Cliente Final", "admin": "🛡️ Administrador",
}
role       = invite.get("role", "parceiro")
role_label = role_labels.get(role, role.capitalize())

try:
    exp_dt  = datetime.fromisoformat(invite.get("expires_at", ""))
    exp_str = exp_dt.strftime("%d/%m/%Y às %H:%M")
except Exception:
    exp_str = invite.get("expires_at", "—")

st.success(f"✅ Convite válido! Perfil: **{role_label}** — expira em {exp_str}")
st.subheader("Preencha seus dados")

with st.form("form_cadastro_parceiro", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1:
        nome     = st.text_input("Nome completo *", placeholder="João da Silva")
        email    = st.text_input("E-mail *", value=invite.get("email", ""), disabled=bool(invite.get("email")))
        telefone = st.text_input("Telefone / WhatsApp *", placeholder="(31) 99999-9999")
    with col2:
        empresa = st.text_input("Nome do negócio", placeholder="Salão Beleza Total")
        cidade  = st.text_input("Cidade *", placeholder="Belo Horizonte")
        estado  = st.selectbox("Estado *", [
            "MG","SP","RJ","ES","BA","GO","DF","PR","SC","RS",
            "MT","MS","AM","PA","CE","PE","MA","PB","RN","AL",
            "SE","PI","TO","RO","AC","RR","AP",
        ])
    senha  = st.text_input("Crie uma senha *", type="password", placeholder="mínimo 8 caracteres")
    senha2 = st.text_input("Confirme a senha *", type="password")
    aceite = st.checkbox("Li e aceito os termos de uso e política de privacidade da Hipnus Cosméticos")
    submitted = st.form_submit_button("✅ Concluir cadastro", use_container_width=True, type="primary")

if submitted:
    erros = []
    if not nome.strip():           erros.append("Nome é obrigatório.")
    if not email.strip():          erros.append("E-mail é obrigatório.")
    elif not validar_email(email): erros.append("E-mail inválido.")
    if not telefone.strip():       erros.append("Telefone é obrigatório.")
    if not cidade.strip():         erros.append("Cidade é obrigatória.")
    if len(senha) < 8:             erros.append("Senha deve ter ao menos 8 caracteres.")
    if senha != senha2:            erros.append("As senhas não coincidem.")
    if not aceite:                 erros.append("Você precisa aceitar os termos de uso.")
    if erros:
        for e in erros:
            st.error(e)
    else:
        payload = {
            "nome": nome.strip(), "email": email.strip(), "telefone": telefone.strip(),
            "empresa": empresa.strip(), "cidade": cidade.strip(), "estado": estado,
            "senha": senha, "role": role, "token": token,
        }
        ok, msg = usar_token(token, payload)
        if ok:
            st.session_state.cadastro_ok = True
            st.rerun()
        else:
            st.error(f"❌ {msg}")
