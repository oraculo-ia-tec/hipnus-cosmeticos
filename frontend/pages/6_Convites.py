"""
6_Convites.py — HIPNUS COSMÉTICOS
====================================
Gerenciamento de convites de cadastro para parceiros e distribuidores.
"""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import requests as http_requests

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
from lib import ui
from lib.auth import require_auth, sidebar_logo, sidebar_user_info, sidebar_logout_button
from lib import components
from lib.invite_db import criar_invite_db
from lib.email_service import send_invite_email, smtp_status

# ─── Setup ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Convites · HIPNUS", page_icon="📨", layout="wide")
ui.inject_theme()
usuario = require_auth(perfis_permitidos=["super_admin", "admin"])
sidebar_logo()
sidebar_user_info()
sidebar_logout_button()

if "_convites_gerados" not in st.session_state:
    st.session_state["_convites_gerados"] = []

API_URL            = st.secrets.get("HIPNUS_API_URL", "http://localhost:8000")
INVITE_EXPIRY_DAYS = 7


def _resolve_app_url() -> str:
    import os
    for getter in [
        lambda: st.secrets.get("APP_BASE_URL"),
        lambda: st.secrets["default"].get("APP_BASE_URL"),
    ]:
        try:
            val = getter()
            if val:
                return val.rstrip("/")
        except Exception:
            pass
    return os.environ.get("HIPNUS_APP_URL", "https://hipnus-cosmeticos.streamlit.app")


def _signup_url(token: str) -> str:
    base = _resolve_app_url().rstrip("/")
    return f"{base}/Cadastro_Parceiro?token={token}"


# ─── Caminhos de criação de convite ──────────────────────────────────────────
def _criar_via_api(email: str, role: str, token_admin: str | None = None) -> dict | None:
    headers = {"Content-Type": "application/json"}
    if token_admin:
        headers["Authorization"] = f"Bearer {token_admin}"
    try:
        resp = http_requests.post(
            f"{API_URL}/api/v1/invites/",
            json={"email": email, "role": role},
            headers=headers, timeout=5,
        )
        if resp.status_code in (200, 201):
            data = resp.json()
            if "token" in data:
                data["signup_url"] = _signup_url(data["token"])
            return data
    except Exception:
        pass
    return None


def _criar_via_db(email: str, role: str, criado_por: str) -> dict | None:
    return criar_invite_db(
        email=email, role=role,
        criado_por=criado_por, app_url=_resolve_app_url(),
    )


def _criar_offline(email: str, role: str, criado_por: str) -> dict:
    token = uuid.uuid4().hex
    signup_url = _signup_url(token)
    return {
        "token":      token,
        "email":      email,
        "role":       role,
        "created_by": criado_por,
        "signup_url": signup_url,
        "expires_at": (datetime.utcnow() + timedelta(days=INVITE_EXPIRY_DAYS)).strftime("%d/%m/%Y"),
        "email_sent": False,
        "origem":     "offline",
    }


# ─── UI Helpers ──────────────────────────────────────────────────────────────
def _badge_role(role: str) -> str:
    return {
        "b2b": "🎤 Profissional", "b2c": "👤 Cliente", "admin": "🛡️ Admin",
    }.get(role, role)


def _card_link(signup_url: str, role: str, criado_por: str) -> None:
    st.html(f"""
    <div style="background:#f3f0ff;border:1.5px solid #c4b5fd;border-radius:12px;
                padding:18px 20px;margin:12px 0;">
        <div style="font-size:.72rem;font-weight:700;letter-spacing:.8px;
                    text-transform:uppercase;color:#7C3AED;margin-bottom:6px;">
            🔗 Link de cadastro — expira em 7 dias
        </div>
        <div style="font-size:.88rem;color:#1A1430;word-break:break-all;background:#fff;
                    padding:10px 14px;border-radius:8px;border:1px solid #ddd5f8;
                    font-family:monospace;">{signup_url}</div>
        <div style="font-size:.75rem;color:#6B6580;margin-top:8px;">
            Perfil: <strong>{_badge_role(role)}</strong>
            &nbsp;·&nbsp; Criado por: <strong>{criado_por}</strong>
        </div>
    </div>""")
    st.text_area(
        "Copie o link:", value=signup_url,
        height=75, key=f"_copy_{signup_url[-8:]}",
    )


# ─── Header ────────────────────────────────────────────────────────────────────
components.page_header(
    title="Convites de Parceiros",
    subtitle="Gerencie convites personalizados para novos distribuidores, salões e parceiros.",
    kicker="Área Admin",
)

tab1, tab2, tab3 = st.tabs(["📨 Enviar Convite", "🔗 Gerar Convite", "📋 Monitorar Convites"])


# ══ TAB 1 — ENVIAR CONVITE ─────────────────────────────────────────────────────────
with tab1:
    components.section_title("Enviar convite por e-mail")

    with st.form("form_enviar_convite", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            email_t1 = st.text_input("E-mail do destinatário", placeholder="parceiro@email.com")
        with col2:
            role_t1 = st.selectbox(
                "Perfil", ["b2b", "b2c", "admin"],
                format_func=lambda r: {
                    "b2b": "Profissional / Salão",
                    "b2c": "Cliente Final",
                    "admin": "Administrador",
                }.get(r, r),
                key="role_t1",
            )
        submitted_t1 = st.form_submit_button(
            "📨 Enviar convite", use_container_width=True, type="primary",
        )

    if submitted_t1:
        if not email_t1 or "@" not in email_t1:
            st.error("⚠️ Informe um e-mail válido.")
        else:
            criado_por = usuario.get("login", "admin")
            with st.spinner("Criando convite..."):
                resultado = _criar_via_api(
                    email_t1, role_t1,
                    token_admin=st.session_state.get("_auth_token"),
                )
            if resultado:
                convite = {**resultado, "origem": resultado.get("origem", "api")}
                st.session_state["_convites_gerados"].insert(0, convite)
                ok, msg = send_invite_email(email_t1, resultado["signup_url"], role_t1)
                if ok:
                    st.success(f"✅ Convite enviado para **{email_t1}**!")
                else:
                    st.warning(f"⚠️ Convite criado, mas o e-mail não pôde ser enviado. Copie o link abaixo.")
                _card_link(resultado["signup_url"], role_t1, criado_por)
            else:
                with st.spinner("Salvando convite..."):
                    resultado = _criar_via_db(email_t1, role_t1, criado_por)
                if resultado:
                    convite = {**resultado, "origem": "db_direto"}
                    st.session_state["_convites_gerados"].insert(0, convite)
                    ok, msg = send_invite_email(email_t1, resultado["signup_url"], role_t1)
                    if ok:
                        st.success(f"✅ Convite enviado para **{email_t1}**!")
                        convite["email_sent"] = True
                    else:
                        st.warning("⚠️ Convite salvo, mas o e-mail não pôde ser enviado. Copie o link abaixo.")
                    _card_link(resultado["signup_url"], role_t1, criado_por)
                else:
                    convite = _criar_offline(email_t1, role_t1, criado_por)
                    st.session_state["_convites_gerados"].insert(0, convite)
                    st.error("❌ Não foi possível salvar o convite. Verifique as configurações e tente novamente.")
                    ok, _ = send_invite_email(email_t1, convite["signup_url"], role_t1)
                    if ok:
                        st.info("📧 E-mail enviado.")
                    _card_link(convite["signup_url"], role_t1, criado_por)


# ══ TAB 2 — GERAR CONVITE MANUAL ────────────────────────────────────────────────────
with tab2:
    components.section_title("Gerar link de convite manual")
    st.caption("Gera o link de cadastro para você copiar e enviar manualmente.")
    with st.form("form_gerar_convite", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            email_t2 = st.text_input("E-mail do destinatário", placeholder="parceiro@email.com")
        with col2:
            role_t2 = st.selectbox(
                "Perfil", ["b2b", "b2c", "admin"],
                format_func=lambda r: {
                    "b2b": "Profissional / Salão",
                    "b2c": "Cliente Final",
                    "admin": "Administrador",
                }.get(r, r),
                key="role_t2",
            )
        submitted_t2 = st.form_submit_button(
            "🔗 Gerar link", use_container_width=True,
        )
    if submitted_t2:
        if not email_t2 or "@" not in email_t2:
            st.error("⚠️ Informe um e-mail válido.")
        else:
            criado_por = usuario.get("login", "admin")
            with st.spinner("Gerando convite..."):
                resultado = (
                    _criar_via_api(email_t2, role_t2, st.session_state.get("_auth_token"))
                    or _criar_via_db(email_t2, role_t2, criado_por)
                )
            if resultado:
                convite = {**resultado, "email_sent": False, "origem": resultado.get("origem", "db_direto")}
                st.success("✅ Link gerado com sucesso!")
            else:
                convite = _criar_offline(email_t2, role_t2, criado_por)
                st.warning("⚠️ Convite gerado em modo temporário. Salve o link abaixo.")
            st.session_state["_convites_gerados"].insert(0, convite)
            _card_link(convite["signup_url"], role_t2, criado_por)


# ══ TAB 3 — MONITORAR ────────────────────────────────────────────────────────────────
with tab3:
    components.section_title("Monitorar convites da sessão")
    convites = st.session_state.get("_convites_gerados", [])
    col_clear, _ = st.columns([1, 3])
    with col_clear:
        if st.button("🗑️ Limpar histórico", use_container_width=True):
            st.session_state["_convites_gerados"] = []
            st.rerun()
    if not convites:
        components.empty_state(
            icon="📨",
            title="Nenhum convite nesta sessão",
            message="Use 'Enviar Convite' ou 'Gerar Convite' para criar um link.",
        )
    else:
        total    = len(convites)
        enviados = sum(1 for c in convites if c.get("email_sent"))
        m1, m2 = st.columns(2)
        m1.metric("Total gerados", total)
        m2.metric("E-mails enviados", enviados)
        components.divider()
        for inv in convites:
            email_val  = inv.get("email", "N/A")
            status_env = "✅ Enviado" if inv.get("email_sent") else "📋 Manual"
            role_badge = _badge_role(inv.get("role", ""))
            label      = f"{email_val} — {status_env} · {role_badge}"
            expira_val = inv.get("expires_at", "—")
            with st.expander(label):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**Perfil:** {role_badge}")
                    st.markdown(f"**E-mail enviado:** {'✅ Sim' if inv.get('email_sent') else '❌ Não'}")
                    st.markdown(f"**Expira:** {expira_val}")
                with col_b:
                    if inv.get("signup_url"):
                        st.code(inv["signup_url"], language=None)
