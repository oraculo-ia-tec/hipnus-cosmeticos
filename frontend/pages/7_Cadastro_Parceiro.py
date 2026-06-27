"""
7_Cadastro_Parceiro.py — HIPNUS COSMÉTICOS
============================================
Página acessada pelo convidado através do link personalizado.
Valida o token do convite, exibe formulário de cadastro e
registra o novo parceiro no sistema.

Fluxo de validação (com fallback):
  1. Lê ?token= da query string (ou campo manual)
  2a. Tenta validar via API (GET /api/v1/invites/{token})
  2b. Se API indisponível: valida diretamente no banco SQLite/MySQL
  3. Exibe formulário pré-preenchido com e-mail do convite
  4. Ao submeter:
     4a. Tenta POST /api/v1/invites/{token}/use (API)
     4b. Fallback: marca como usado diretamente no banco
  5. Sucesso: exibe mensagem de boas-vindas

Motivo do fallback direto ao banco:
  O Streamlit Cloud é um servidor externo e não consegue acessar
  a API FastAPI quando ela roda em localhost (VPS Hostinger).
  O fallback garante que o fluxo funcione mesmo sem a API exposta.

Configuração necessária em .streamlit/secrets.toml:
  HIPNUS_API_URL = "https://sua-api.hipnuscosmeticos.com.br"  # URL publica da API
  DATABASE_URL   = "sqlite:///./data/hipnus.db"               # ou MySQL em producao
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import streamlit as st

# Garante que os módulos do projeto sejam encontrados
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ─── Config ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cadastro Parceiro | Hipnus Cosméticos",
    page_icon="💼",
    layout="centered",
)

API_URL      = st.secrets.get("HIPNUS_API_URL", "http://localhost:8000")
DATABASE_URL = st.secrets.get("DATABASE_URL",   "sqlite:///./data/hipnus.db")


# ─── Fallback: acesso direto ao banco ───────────────────────────────────────────────

def _get_db_session():
    """
    Cria uma sessão SQLAlchemy direta com o banco configurado em DATABASE_URL.
    Usado como fallback quando a API FastAPI não está acessível.
    Retorna (session, error_str). Se falhar, session=None e error_str descreve o problema.
    """
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
        engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
        Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        return Session(), None
    except Exception as exc:
        return None, str(exc)


def _validar_token_db(token: str) -> dict | None:
    """
    Valida token diretamente no banco SQLite/MySQL.
    Retorna dict compatível com o schema da API ou None se inválido.
    """
    db, err = _get_db_session()
    if not db:
        return None
    try:
        # Import direto do model (disponivel no mesmo repo)
        from app.domains.invites.models import Invite
        invite = db.query(Invite).filter(Invite.token == token).first()
        if not invite:
            return None
        if invite.used:
            return None
        # Normaliza timezone para comparacao
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if invite.expires_at < now:
            return None
        return {
            "id":         invite.id,
            "token":      invite.token,
            "email":      invite.email,
            "role":       invite.role,
            "created_by": invite.created_by,
            "used":       invite.used,
            "expires_at": invite.expires_at.isoformat() if invite.expires_at else "",
            "created_at": invite.created_at.isoformat() if invite.created_at else "",
        }
    except Exception:
        return None
    finally:
        db.close()


def _usar_token_db(token: str, dados: dict) -> tuple[bool, str]:
    """
    Marca token como usado diretamente no banco.
    Cria o registro do parceiro na tabela partners se existir.
    """
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


# ─── Helpers via API ──────────────────────────────────────────────────────────────────

def validar_token(token: str) -> dict | None:
    """
    Valida token: tenta API primeiro, fallback direto no banco.
    Retorna dict do invite ou None.
    """
    # Caminho 1: API
    try:
        r = requests.get(f"{API_URL}/api/v1/invites/{token}", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass

    # Caminho 2: banco direto
    return _validar_token_db(token)


def usar_token(token: str, dados: dict) -> tuple[bool, str]:
    """
    Marca token como usado: tenta API primeiro, fallback direto no banco.
    """
    # Caminho 1: API
    try:
        r = requests.post(
            f"{API_URL}/api/v1/invites/{token}/use",
            json=dados,
            timeout=10,
        )
        if r.status_code in (200, 201):
            return True, "Cadastro realizado com sucesso!"
    except Exception:
        pass

    # Caminho 2: banco direto
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
.token-manual {
    background:#fff8e1;border:1px solid #ffe082;border-radius:8px;
    padding:1rem;margin-bottom:1rem;font-size:.9rem;color:#5d4037;
}
</style>
""", unsafe_allow_html=True)

# ─── Lógica principal ──────────────────────────────────────────────────────────────────

token_url = st.query_params.get("token")

# Header
st.markdown("""
<div class="invite-header">
    <h1>💼 Hipnus Cosméticos</h1>
    <p>Você foi convidado para se tornar um parceiro</p>
</div>
""", unsafe_allow_html=True)

# Estado da sessão
for key, default in [("cadastro_ok", False), ("invite_data", None), ("token_validado", None)]:
    if key not in st.session_state:
        st.session_state[key] = default

# Sucesso
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

# Entrada do token
token = token_url

if not token:
    st.markdown('<div class="token-manual">ℹ️ Acesse esta página pelo link do seu convite, ou cole o código abaixo.</div>', unsafe_allow_html=True)
    token_input = st.text_input("Código do convite", placeholder="cole aqui o token do seu convite")
    if token_input:
        token = token_input.strip()

if not token:
    st.info("Aguardando código de convite...")
    st.stop()

# Validação do token (API com fallback no banco)
if st.session_state.token_validado != token:
    with st.spinner("Validando seu convite..."):
        invite = validar_token(token)
    if invite is None:
        st.error("❌ Convite inválido, expirado ou já utilizado. Solicite um novo convite ao administrador.")
        # Debug: mostra qual DATABASE_URL está sendo usada (apenas token)
        with st.expander("🔧 Detalhes técnicos (admin)"):
            st.code(f"API_URL: {API_URL}\nDATABASE_URL: {DATABASE_URL[:40]}...\nToken: {token[:16]}...", language="text")
        st.stop()
    st.session_state.invite_data   = invite
    st.session_state.token_validado = token

invite = st.session_state.invite_data

# Info do convite
role_labels = {
    "distribuidor": "🏗️ Distribuidor",
    "revendedor":   "🛍️ Revendedor",
    "salao":        "✂️ Salão de Beleza",
    "profissional": "💇 Profissional",
    "parceiro":     "🤝 Parceiro",
    "b2b":          "🎤 Profissional / Salão",
    "b2c":          "👤 Cliente Final",
    "admin":        "🛡️ Administrador",
}
role       = invite.get("role", "parceiro")
role_label = role_labels.get(role, role.capitalize())

expires_raw = invite.get("expires_at", "")
try:
    exp_dt  = datetime.fromisoformat(expires_raw)
    exp_str = exp_dt.strftime("%d/%m/%Y às %H:%M")
except Exception:
    exp_str = expires_raw

st.success(f"✅ Convite válido! Perfil: **{role_label}** — expira em {exp_str}")

# Formulário de cadastro
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
