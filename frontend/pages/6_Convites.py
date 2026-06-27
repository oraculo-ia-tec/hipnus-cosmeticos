"""
6_Convites.py — HIPNUS COSMÉTICOS
====================================
Gerenciamento de convites de cadastro para parceiros e distribuidores.

Fluxo de persistência (3 caminhos em ordem de prioridade):
  1. API disponível       → POST /api/v1/invites/ (persiste via FastAPI)
  2. API indisponível     → persiste no banco DIRETAMENTE via invite_db
  3. API + banco falham   → token offline (não pode ser validado)

Fix v9:
  - Corrigido SyntaxError Python 3.11: backslash dentro de f-strings
  - signup_url corrigida para rota real do Streamlit Cloud
  - usa lib.invite_db standalone (sem dependência do app/)
"""
from __future__ import annotations

import smtplib
import ssl
import sys
import uuid
from datetime import datetime, timedelta, timezone
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate
from pathlib import Path

import requests as http_requests

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
from lib import ui
from lib.auth import require_auth, sidebar_logo, sidebar_user_info, sidebar_logout_button
from lib import components
from lib.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_USE_TLS, SMTP_USE_SSL, SMTP_REMETENTE
from lib.db_utils import resolve_db_url
from lib.invite_db import criar_invite_db  # camada DB standalone

# ─── Setup ────────────────────────────────────────────────────────────────────
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


# ─── Caminho 1: API ───────────────────────────────────────────────────────────
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


# ─── Caminho 2: banco direto via invite_db ─────────────────────────────────────
def _criar_via_db(email: str, role: str, criado_por: str) -> dict | None:
    return criar_invite_db(
        email=email,
        role=role,
        criado_por=criado_por,
        app_url=_resolve_app_url(),
    )


# ─── Caminho 3: offline ────────────────────────────────────────────────────────
def _criar_offline(email: str, role: str, criado_por: str) -> dict:
    token      = uuid.uuid4().hex
    signup_url = _signup_url(token)
    return {
        "token":      token,
        "email":      email,
        "role":       role,
        "created_by": criado_por,
        "signup_url": signup_url,
        "expires_at": (
            datetime.utcnow() + timedelta(days=INVITE_EXPIRY_DAYS)
        ).strftime("%d/%m/%Y"),
        "email_sent": False,
        "origem":     "offline",
    }


# ─── SMTP ──────────────────────────────────────────────────────────────────────
def _enviar_smtp(destinatario: str, signup_url: str, role: str) -> tuple[bool, str]:
    if not SMTP_USER or not SMTP_PASS:
        return False, "Credenciais SMTP não configuradas."
    role_label = {
        "b2b":   "Profissional / Salão",
        "b2c":   "Cliente Final",
        "admin": "Administrador",
    }.get(role, role)
    expira    = (datetime.utcnow() + timedelta(days=INVITE_EXPIRY_DAYS)).strftime("%d/%m/%Y")
    text_body = (
        f"Você foi convidado para HIPNUS COSMETICOS!\n\n"
        f"Perfil: {role_label}\nVálidade: {expira}\n\nLink de cadastro:\n{signup_url}\n"
    )
    html_body = f"""\
<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#F6F4FB;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#F6F4FB;padding:32px 0;">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" border="0"
       style="background:#fff;border-radius:16px;border:1px solid #E7E3F2;">
<tr><td style="background:#7C3AED;padding:28px 40px;text-align:center;border-radius:16px 16px 0 0;">
  <div style="font-size:1.3rem;font-weight:800;color:#fff;">HIPNUS COSM&#201;TICOS</div>
  <div style="font-size:.72rem;color:rgba(255,255,255,.75);letter-spacing:2px;
              text-transform:uppercase;margin-top:4px;">Convite de Acesso</div>
</td></tr>
<tr><td style="padding:32px 40px;">
  <p style="font-size:1rem;color:#1A1430;margin:0 0 20px;line-height:1.6;">
    Voc&#234; recebeu um convite exclusivo como <strong>{role_label}</strong>.
    V&#225;lido at&#233; <strong>{expira}</strong>.
  </p>
  <table cellpadding="0" cellspacing="0" border="0" width="100%">
  <tr><td align="center" style="padding:0 0 20px;">
    <a href="{signup_url}"
       style="display:inline-block;background:#7C3AED;color:#fff;text-decoration:none;
              font-size:15px;font-weight:bold;padding:14px 40px;border-radius:10px;">
      Concluir meu cadastro
    </a>
  </td></tr></table>
  <p style="font-size:.8rem;color:#6B6580;margin:0 0 8px;">Ou copie e cole o link no navegador:</p>
  <div style="background:#F6F4FB;border:1px solid #E7E3F2;border-radius:6px;padding:10px 14px;">
    <span style="font-family:monospace;font-size:12px;color:#7C3AED;
                 word-break:break-all;">{signup_url}</span>
  </div>
</td></tr>
<tr><td style="background:#F6F4FB;padding:14px 40px;text-align:center;
              border-radius:0 0 16px 16px;border-top:1px solid #E7E3F2;">
  <p style="color:#9CA3AF;font-size:11px;margin:0;">HIPNUS COSM&#201;TICOS &copy; 2026</p>
</td></tr></table></td></tr></table></body></html>"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header("Seu convite para HIPNUS COSMETICOS", "utf-8").encode()
    msg["From"]    = formataddr(("HIPNUS COSMETICOS", SMTP_REMETENTE))
    msg["To"]      = destinatario
    msg["Date"]    = formatdate(localtime=False)
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html",  "utf-8"))
    try:
        if SMTP_USE_SSL:
            with smtplib.SMTP_SSL(
                SMTP_HOST, SMTP_PORT,
                context=ssl.create_default_context(), timeout=15,
            ) as s:
                s.login(SMTP_USER, SMTP_PASS)
                s.sendmail(SMTP_REMETENTE, destinatario, msg.as_string())
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as s:
                s.ehlo()
                if SMTP_USE_TLS:
                    s.starttls(context=ssl.create_default_context())
                    s.ehlo()
                s.login(SMTP_USER, SMTP_PASS)
                s.sendmail(SMTP_REMETENTE, destinatario, msg.as_string())
        return True, "E-mail enviado."
    except smtplib.SMTPAuthenticationError:
        return False, "Falha de autenticação SMTP."
    except Exception as exc:
        return False, str(exc)


# ─── UI Helpers ────────────────────────────────────────────────────────────────
def _badge_role(role: str) -> str:
    return {
        "b2b": "🎤 Profissional", "b2c": "👤 Cliente", "admin": "🛡️ Admin",
    }.get(role, role)

def _badge_origem(origem: str) -> str:
    return {
        "api": "🔵 API", "db_direto": "🟢 Banco Direto", "offline": "🟡 Offline",
    }.get(origem, origem)

def _card_link(signup_url: str, role: str, criado_por: str, origem: str) -> None:
    st.html(f"""
    <div style="background:#f3f0ff;border:1.5px solid #c4b5fd;border-radius:12px;
                padding:18px 20px;margin:12px 0;">
        <div style="font-size:.72rem;font-weight:700;letter-spacing:.8px;
                    text-transform:uppercase;color:#7C3AED;margin-bottom:6px;">
            🔗 Link de cadastro — expira em 7 dias
        </div>
        <div style="font-size:.88rem;color:#1A1430;word-break:break-all;background:#fff;
                    padding:10px 14px;border-radius:8px;border:1px solid #ddd5f8;
                    font-family:monospace;">
            {signup_url}
        </div>
        <div style="font-size:.75rem;color:#6B6580;margin-top:8px;">
            Perfil: <strong>{_badge_role(role)}</strong>
            &nbsp;·&nbsp; Criado por: <strong>{criado_por}</strong>
            &nbsp;·&nbsp; Origem: {_badge_origem(origem)}
        </div>
    </div>""")
    st.text_area(
        "Copie o link:", value=signup_url,
        height=75, key=f"_copy_{signup_url[-8:]}",
    )

def _aviso_smtp() -> None:
    if not SMTP_USER or not SMTP_PASS:
        st.warning("⚙️ SMTP não configurado. Verifique o bloco [email] nos Streamlit Secrets.")
    else:
        smtp_info = f"{SMTP_HOST}:{SMTP_PORT} — {SMTP_REMETENTE}"
        st.html(f"""
        <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;
                    padding:10px 16px;font-size:.82rem;color:#166534;margin-bottom:12px;">
            ✅ <strong>SMTP:</strong> {smtp_info}
        </div>""")

def _debug_info() -> None:
    db_url  = resolve_db_url()
    app_url = _resolve_app_url()
    ex_url  = _signup_url("TOKEN_EXEMPLO")
    with st.expander("🔧 Info técnica (admin)"):
        st.code(
            f"API_URL:         {API_URL}\n"
            f"DATABASE_URL:    {db_url}\n"
            f"APP_BASE_URL:    {app_url}\n"
            f"SIGNUP_URL ex:   {ex_url}",
            language="text",
        )


# ─── Header ────────────────────────────────────────────────────────────────────
components.page_header(
    title="Convites de Parceiros",
    subtitle="Gerencie convites personalizados para novos distribuidores, salões e parceiros.",
    kicker="Área Admin",
)
_debug_info()

tab1, tab2, tab3 = st.tabs(["📨 Enviar Convite", "🔗 Gerar Convite", "📋 Monitorar Convites"])


# ══ TAB 1 — ENVIAR CONVITE ─────────────────────────────────────────────────────
with tab1:
    components.section_title("Enviar convite por e-mail")
    st.caption("Prioridade: 1º API, 2º banco direto (path absoluto), 3º offline.")
    _aviso_smtp()

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
                ok, msg = _enviar_smtp(email_t1, resultado["signup_url"], role_t1)
                if ok:
                    st.success(f"✅ Convite (API) + e-mail enviado para **{email_t1}**!")
                else:
                    st.warning(f"⚠️ Convite salvo, e-mail falhou: {msg}")
                _card_link(resultado["signup_url"], role_t1, criado_por, "api")
            else:
                with st.spinner("API indisponível. Salvando no banco..."):
                    resultado = _criar_via_db(email_t1, role_t1, criado_por)
                if resultado:
                    convite = {**resultado, "origem": "db_direto"}
                    st.session_state["_convites_gerados"].insert(0, convite)
                    ok, msg = _enviar_smtp(email_t1, resultado["signup_url"], role_t1)
                    if ok:
                        st.success(
                            f"✅ Convite salvo no banco + e-mail enviado para **{email_t1}**!"
                        )
                        convite["email_sent"] = True
                    else:
                        st.warning(
                            f"⚠️ Token salvo no banco, e-mail falhou: {msg}. "
                            "Copie o link abaixo."
                        )
                    _card_link(resultado["signup_url"], role_t1, criado_por, "db_direto")
                else:
                    convite = _criar_offline(email_t1, role_t1, criado_por)
                    st.session_state["_convites_gerados"].insert(0, convite)
                    st.error(
                        "❌ API e banco indisponíveis. Token offline — "
                        "**o link NÃO será validado**. "
                        "Verifique DATABASE_URL nos Streamlit Secrets."
                    )
                    ok, _ = _enviar_smtp(email_t1, convite["signup_url"], role_t1)
                    if ok:
                        st.info("📧 E-mail enviado, mas convite offline não pode ser validado.")
                    _card_link(convite["signup_url"], role_t1, criado_por, "offline")


# ══ TAB 2 — GERAR CONVITE MANUAL ──────────────────────────────────────────────
with tab2:
    components.section_title("Gerar link de convite manual")
    st.caption("Gera o link e salva no banco. Copie e envie manualmente.")
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
                convite = {
                    **resultado,
                    "email_sent": False,
                    "origem":     resultado.get("origem", "db_direto"),
                }
                st.success("📋 Convite salvo no banco.")
            else:
                convite = _criar_offline(email_t2, role_t2, criado_por)
                st.warning("⚠️ Banco indisponível. Token offline.")
            st.session_state["_convites_gerados"].insert(0, convite)
            _card_link(
                convite["signup_url"], role_t2, criado_por, convite["origem"],
            )


# ══ TAB 3 — MONITORAR ──────────────────────────────────────────────────────────
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
        banco    = sum(1 for c in convites if c.get("origem") in ("api", "db_direto"))
        offline  = sum(1 for c in convites if c.get("origem") == "offline")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total", total)
        m2.metric("E-mail enviado", enviados)
        m3.metric("Salvo no banco", banco)
        m4.metric("Offline", offline)
        components.divider()
        for inv in convites:
            # Variaveis intermediarias para evitar backslash em f-string (Python 3.11)
            email_val   = inv.get("email", "N/A")
            status_env  = "✅ Enviado" if inv.get("email_sent") else "📋 Manual"
            role_badge  = _badge_role(inv.get("role", ""))
            orig_badge  = _badge_origem(inv.get("origem", ""))
            label       = f"{email_val} — {status_env} · {role_badge} · {orig_badge}"

            email_ok    = "✅ Sim" if inv.get("email_sent") else "❌ Não"
            expira_val  = inv.get("expires_at", "—")
            token_val   = inv.get("token", "N/A")

            with st.expander(label):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**Perfil:** {role_badge}")
                    st.markdown(f"**E-mail enviado:** {email_ok}")
                    st.markdown(f"**Expira:** {expira_val}")
                    st.markdown(f"**Origem:** {orig_badge}")
                with col_b:
                    st.markdown(f"**Token:** `{token_val}`")
                    if inv.get("signup_url"):
                        st.code(inv["signup_url"], language=None)
