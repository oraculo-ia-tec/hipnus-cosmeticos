"""
7_Cadastro_Parceiro.py — HIPNUS COSMÉTICOS
============================================
Página acessada pelo convidado através do link personalizado.

Fix v7: usa lib.db_utils.get_db_session() que resolve o path SQLite
para ABSOLUTO usando PROJECT_ROOT, garantindo que o mesmo .db
usado em 6_Convites seja acessado aqui.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import streamlit as st

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Adiciona frontend ao path para importar lib
_FRONTEND = Path(__file__).resolve().parents[1]
if str(_FRONTEND) not in sys.path:
    sys.path.insert(0, str(_FRONTEND))

from lib.db_utils import get_db_session, resolve_db_url

# ─── Config ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cadastro Parceiro | Hipnus Cosméticos",
    page_icon="💼", layout="centered",
)

API_URL = st.secrets.get("HIPNUS_API_URL", "http://localhost:8000")


# ─── Validação via API com fallback no banco ─────────────────────────────────────────

def _validar_token_db(token: str) -> dict | None:
    db, err = get_db_session()
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
    db, err = get_db_session()
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
    background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);
    border-radius:16px;padding:2.5rem 2rem 2rem;text-align:center;margin-bottom:2rem;color:white;
}
.invite-header h1{font-size:2rem;margin-bottom:.25rem;}
.invite-header p{opacity:.8;font-size:1rem;margin:0;}
.success-box{
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
        <p>Bem-vindo à família Hipnus Cosméticos.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🏠 Ir para a Home", use_container_width=True):
        st.switch_page("pages/1_Home.py")
    st.stop()

token = token_url
if not token:
    st.info("ℹ️ Acesse esta página pelo link do seu convite, ou cole o código abaixo.")
    token_input = st.text_input("Código do convite", placeholder="cole aqui o token")
    if token_input:
        token = token_input.strip()

if not token:
    st.stop()

# Validação
if st.session_state.token_validado != token:
    with st.spinner("Validando seu convite..."):
        invite = validar_token(token)
    if invite is None:
        st.error("❌ Convite inválido, expirado ou já utilizado. Solicite um novo convite ao administrador.")
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

role_labels = {
    "distribuidor": "🏗️ Distribuidor", "revendedor": "🛍️ Revendedor",
    "salao": "✂️ Salão", "profissional": "💇 Profissional",
    "parceiro": "🤝 Parceiro", "b2b": "🎤 Profissional / Salão",
    "b2c": "👤 Cliente Final", "admin": "🛡️ Administrador",
}
role       = invite.get("role", "parceiro")
role_label = role_labels.get(role, role.capitalize())
try:
    exp_str = datetime.fromisoformat(invite.get("expires_at", "")).strftime("%d/%m/%Y às %H:%M")
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
        for e in erros: st.error(e)
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
