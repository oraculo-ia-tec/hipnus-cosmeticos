"""
6_Convites.py — HIPNUS COSMÉTICOS
====================================
Gerenciamento de convites de cadastro para parceiros e distribuidores.

Estrutura em 3 abas:
  tab1 — Enviar Convite  : salva token na API (POST /api/v1/invites/) e envia
                           e-mail DIRETAMENTE via SMTP Hostinger.
                           Fallback offline se a API estiver indisponível.
  tab2 — Gerar Convite   : gera token/link offline para envio manual.
  tab3 — Monitorar       : lista e monitora todos os convites gerados na sessão.

Fluxo correto (Tab1):
  1. Chama POST /api/v1/invites/ → persiste token no banco (FastAPI)
  2. Retorna signup_url com ?token=TOKEN
  3. Exibe card com link e confirmação de e-mail
  4. Fallback: se API indisponível, gera token local + envia SMTP direto

Correções v5:
  - Tab1 agora chama a API para persistir o token antes de enviar o e-mail.
    Sem isso, 7_Cadastro_Parceiro.py não encontra o token no banco e
    exibe 'Convite inválido'.
  - Fallback SMTP direto mantido para quando a API não está disponível.
  - signup_url usa ?token= em todos os caminhos.

Credenciais esperadas em .streamlit/secrets.toml:
  [email]
  EMAIL_HOST      = "smtp.hostinger.com"
  EMAIL_PORT      = "587"
  EMAIL_USERNAME  = "contato@oraculosia.site"
  EMAIL_PASSWORD  = "..."
  EMAIL_USE_TLS   = "true"
  EMAIL_USE_SSL   = "false"
  EMAIL_REMETENTE = "contato@oraculosia.site"
"""
from __future__ import annotations

import smtplib
import ssl
import sys
import uuid
from datetime import datetime, timedelta
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate
from pathlib import Path

import requests as http_requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from lib import ui
from lib.auth import require_auth, sidebar_logo, sidebar_user_info, sidebar_logout_button
from lib import components
from lib.config import APP_URL, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_USE_TLS, SMTP_USE_SSL, SMTP_REMETENTE

# ─── Setup ───────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Convites · HIPNUS", page_icon="📨", layout="wide")
ui.inject_theme()
usuario = require_auth(perfis_permitidos=["super_admin", "admin"])
sidebar_logo()
sidebar_user_info()
sidebar_logout_button()

if "_convites_gerados" not in st.session_state:
    st.session_state["_convites_gerados"] = []

API_URL = st.secrets.get("HIPNUS_API_URL", "http://localhost:8000")


# ─── Helper: criar convite via API (persiste no banco) ────────────────────────
def _criar_convite_via_api(
    email: str,
    role: str,
    token_admin: str | None = None,
) -> dict | None:
    """
    Chama POST /api/v1/invites/ para criar e persistir o convite no banco.

    A API retorna signup_url com ?token=TOKEN já pronto.
    O e-mail é enviado pelo próprio service.py do backend.

    Retorna o dict do convite criado ou None em caso de falha.
    """
    headers = {"Content-Type": "application/json"}
    if token_admin:
        headers["Authorization"] = f"Bearer {token_admin}"
    try:
        resp = http_requests.post(
            f"{API_URL}/api/v1/invites/",
            json={"email": email, "role": role},
            headers=headers,
            timeout=10,
        )
        if resp.status_code in (200, 201):
            return resp.json()
        return None
    except Exception:
        return None


# ─── Helper: fallback SMTP direto (sem API) ──────────────────────────────────
def _gerar_token_local(email: str, role: str, criado_por: str) -> dict:
    """
    Gera token localmente como fallback quando a API não está disponível.
    signup_url usa ?token= para compatibilidade com 7_Cadastro_Parceiro.py.
    ATENÇÃO: token gerado localmente NÃO é persistido no banco.
    """
    token      = uuid.uuid4().hex
    signup_url = f"{APP_URL}/Cadastro_Parceiro?token={token}"
    expires_at = datetime.utcnow() + timedelta(days=7)
    return {
        "token":      token,
        "email":      email,
        "role":       role,
        "created_by": criado_por,
        "signup_url": signup_url,
        "expires_at": expires_at.strftime("%d/%m/%Y %H:%M") + " UTC",
        "email_sent": False,
        "origem":     "offline",
    }


def _enviar_email_smtp_direto(destinatario: str, signup_url: str, role: str, token: str) -> tuple[bool, str]:
    """
    Fallback: envia e-mail diretamente via SMTP quando a API não está disponível.
    Usado apenas quando POST /api/v1/invites/ falha.
    """
    if not SMTP_USER or not SMTP_PASS:
        return False, "Credenciais SMTP não configuradas."

    role_label = {"b2b": "Profissional / Salão", "b2c": "Cliente Final", "admin": "Administrador"}.get(role, role)
    expira     = (datetime.utcnow() + timedelta(days=7)).strftime("%d/%m/%Y")

    text_body = (
        f"Voce foi convidado para a plataforma HIPNUS COSMETICOS!\n\n"
        f"Perfil: {role_label}\nValidade: {expira}\n\n"
        f"Link de cadastro:\n{signup_url}\n\n"
        f"HIPNUS COSMETICOS - www.hipnuscosmeticos.com.br"
    )

    html_body = f"""\
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#F6F4FB;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#F6F4FB;padding:32px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" border="0"
             style="background:#ffffff;border-radius:16px;border:1px solid #E7E3F2;">
        <tr>
          <td style="background:#7C3AED;padding:32px 40px;text-align:center;border-radius:16px 16px 0 0;">
            <div style="font-size:1.3rem;font-weight:800;color:#fff;font-family:Arial,sans-serif;">HIPNUS COSM&#201;TICOS</div>
            <div style="font-size:.72rem;color:rgba(255,255,255,.75);letter-spacing:2px;text-transform:uppercase;margin-top:4px;font-family:Arial,sans-serif;">Convite de Acesso</div>
          </td>
        </tr>
        <tr>
          <td style="padding:36px 40px 28px;">
            <p style="font-size:1rem;color:#1A1430;margin:0 0 16px;font-family:Arial,sans-serif;">Ol&#225;,</p>
            <p style="font-size:1rem;color:#1A1430;margin:0 0 20px;line-height:1.6;font-family:Arial,sans-serif;">
              Voc&#234; recebeu um convite exclusivo para se cadastrar na plataforma
              <strong>HIPNUS COSM&#201;TICOS</strong> como <strong>{role_label}</strong>.
              O convite &#233; v&#225;lido at&#233; <strong>{expira}</strong>.
            </p>
            <table cellpadding="0" cellspacing="0" border="0" width="100%">
              <tr><td align="center" style="padding:0 0 32px;">
                <a href="{signup_url}"
                   style="display:inline-block;background:#7C3AED;color:#ffffff;text-decoration:none;
                          font-size:15px;font-weight:bold;padding:14px 40px;border-radius:10px;
                          font-family:Arial,sans-serif;">Concluir meu cadastro</a>
              </td></tr>
            </table>
            <table cellpadding="0" cellspacing="0" border="0" width="100%">
              <tr><td style="background:#F6F4FB;border:1px solid #E7E3F2;border-radius:6px;padding:10px 14px;">
                <span style="font-family:Courier New,monospace;font-size:12px;color:#7C3AED;word-break:break-all;">{signup_url}</span>
              </td></tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="background:#F6F4FB;padding:16px 40px;text-align:center;border-radius:0 0 16px 16px;border-top:1px solid #E7E3F2;">
            <p style="color:#9CA3AF;font-size:11px;margin:0;font-family:Arial,sans-serif;">HIPNUS COSM&#201;TICOS &middot; (31) 98321-3343 &middot; www.hipnuscosmeticos.com.br</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"]      = Header("Seu convite para a plataforma HIPNUS COSMETICOS", "utf-8").encode()
    msg["From"]         = formataddr(("HIPNUS COSMETICOS", SMTP_REMETENTE))
    msg["To"]           = destinatario
    msg["Date"]         = formatdate(localtime=False)
    msg["X-Mailer"]     = "HIPNUS-Convites/5.0"
    msg["MIME-Version"] = "1.0"
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html",  "utf-8"))

    try:
        if SMTP_USE_SSL:
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=15) as s:
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
        return True, "E-mail enviado com sucesso (fallback SMTP direto)."
    except smtplib.SMTPAuthenticationError:
        return False, "Falha de autenticação SMTP."
    except smtplib.SMTPConnectError:
        return False, f"Não foi possível conectar a {SMTP_HOST}:{SMTP_PORT}."
    except Exception as exc:
        return False, f"Erro inesperado: {exc}"


# ─── Badges ──────────────────────────────────────────────────────────────────
def _badge_role(role: str) -> str:
    return {"b2b": "🎤 Profissional", "b2c": "👤 Cliente", "admin": "🛡️ Admin"}.get(role, role)


def _badge_origem(origem: str) -> str:
    return {
        "api":         "🔵 API + SMTP",
        "smtp_direto": "🟢 SMTP Direto",
        "offline":     "🟡 Offline",
    }.get(origem, origem)


def _card_link(signup_url: str, role: str, criado_por: str, origem: str) -> None:
    st.html(f"""
    <div style="background:#f3f0ff;border:1.5px solid #c4b5fd;border-radius:12px;
                padding:18px 20px;margin:12px 0;">
        <div style="font-size:.72rem;font-weight:700;letter-spacing:.8px;
                    text-transform:uppercase;color:#7C3AED;margin-bottom:6px;">
            🔗 Link de cadastro — expira em 7 dias
        </div>
        <div style="font-size:.88rem;color:#1A1430;word-break:break-all;
                    background:#fff;padding:10px 14px;border-radius:8px;
                    border:1px solid #ddd5f8;font-family:monospace;">
            {signup_url}
        </div>
        <div style="font-size:.75rem;color:#6B6580;margin-top:8px;">
            Perfil: <strong>{_badge_role(role)}</strong> &nbsp;·&nbsp;
            Criado por: <strong>{criado_por}</strong> &nbsp;·&nbsp;
            Origem: {_badge_origem(origem)}
        </div>
    </div>
    """)
    st.text_area(
        "Copie o link:",
        value=signup_url,
        height=75,
        help="Selecione e copie (Ctrl+C / Cmd+C)",
        key=f"_copy_{signup_url[-8:]}",
    )


def _aviso_smtp_config() -> None:
    if not SMTP_USER or not SMTP_PASS:
        st.html("""
        <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:10px;
                    padding:12px 16px;font-size:.82rem;color:#92400e;margin-bottom:12px;">
            <strong>⚙️ SMTP não configurado.</strong> Verifique o bloco [email] nos Streamlit Secrets.
        </div>
        """)
    else:
        st.html(f"""
        <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;
                    padding:10px 16px;font-size:.82rem;color:#166534;margin-bottom:12px;">
            ✅ <strong>SMTP configurado:</strong> {SMTP_HOST}:{SMTP_PORT}
            — remetente: <code>{SMTP_REMETENTE}</code>
        </div>
        """)


# ─── Header ──────────────────────────────────────────────────────────────────
components.page_header(
    title="Convites de Parceiros",
    subtitle="Gerencie convites personalizados para novos distribuidores, salões e parceiros.",
    kicker="Área Admin",
)

tab1, tab2, tab3 = st.tabs(["📨 Enviar Convite", "🔗 Gerar Convite", "📋 Monitorar Convites"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ENVIAR CONVITE (API primeiro, SMTP direto como fallback)
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    components.section_title("Enviar convite por e-mail")
    st.caption(
        "Persiste o token na API (banco de dados) e envia o e-mail via SMTP Hostinger. "
        "Se a API não estiver disponível, usa fallback SMTP direto (token não persistido)."
    )
    _aviso_smtp_config()

    with st.form("form_enviar_convite", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            email_t1 = st.text_input("E-mail do destinatário", placeholder="parceiro@email.com")
        with col2:
            role_t1 = st.selectbox(
                "Perfil do convidado",
                ["b2b", "b2c", "admin"],
                format_func=lambda r: {
                    "b2b": "Profissional / Salão",
                    "b2c": "Cliente Final",
                    "admin": "Administrador",
                }.get(r, r),
                key="role_t1",
            )
        submitted_t1 = st.form_submit_button(
            "📨 Enviar convite por e-mail",
            use_container_width=True,
            type="primary",
        )

    if submitted_t1:
        if not email_t1 or "@" not in email_t1:
            st.error("⚠️ Informe um e-mail válido para o destinatário.")
        else:
            criado_por = usuario.get("login", "admin")

            # ── Caminho 1: API disponível → persiste no banco ──────────────
            with st.spinner(f"Criando convite para {email_t1}..."):
                resultado_api = _criar_convite_via_api(
                    email=email_t1,
                    role=role_t1,
                    token_admin=st.session_state.get("_auth_token"),
                )

            if resultado_api:
                signup_url = resultado_api.get("signup_url", "")
                email_sent = resultado_api.get("email_sent", False)
                convite = {
                    "token":      resultado_api.get("token", ""),
                    "email":      email_t1,
                    "role":       role_t1,
                    "created_by": criado_por,
                    "signup_url": signup_url,
                    "expires_at": resultado_api.get("expires_at", "7 dias"),
                    "email_sent": email_sent,
                    "origem":     "api",
                }
                st.session_state["_convites_gerados"].insert(0, convite)

                if email_sent:
                    st.success(f"✅ Convite criado e e-mail enviado para **{email_t1}**!")
                else:
                    st.warning(
                        f"✅ Convite criado no banco para **{email_t1}**, "
                        "mas o e-mail não pôde ser enviado pelo backend. "
                        "Copie o link abaixo e envie manualmente."
                    )
                _card_link(signup_url, role_t1, criado_por, "api")

            else:
                # ── Caminho 2: API indisponível → fallback SMTP direto ─────
                st.warning(
                    "⚠️ API indisponível — usando fallback SMTP direto. "
                    "**O token não será persistido no banco.** "
                    "O convidado precisará usar este link antes que o banco seja atualizado."
                )
                convite = _gerar_token_local(email_t1, role_t1, criado_por)

                with st.spinner(f"Enviando e-mail para {email_t1} via {SMTP_HOST}..."):
                    ok, msg_smtp = _enviar_email_smtp_direto(
                        destinatario=email_t1,
                        signup_url=convite["signup_url"],
                        role=role_t1,
                        token=convite["token"],
                    )

                convite["email_sent"] = ok
                convite["origem"]     = "smtp_direto" if ok else "offline"
                st.session_state["_convites_gerados"].insert(0, convite)

                if ok:
                    st.success(f"✅ E-mail enviado para **{email_t1}** (fallback SMTP).")
                else:
                    st.error(f"❌ Falha ao enviar e-mail.\n\n**Detalhe:** {msg_smtp}")
                    st.info("💡 Copie o link abaixo e envie manualmente ao convidado.")
                _card_link(convite["signup_url"], role_t1, criado_por, convite["origem"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — GERAR CONVITE (offline / manual)
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    components.section_title("Gerar link de convite manual")
    st.caption(
        "Gera apenas o token e o link de cadastro localmente, sem enviar e-mail. "
        "Copie o link e envie manualmente ao convidado por WhatsApp, Instagram ou outro canal."
    )

    with st.form("form_gerar_convite", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            email_t2 = st.text_input(
                "E-mail do destinatário (para registro)",
                placeholder="parceiro@email.com",
            )
        with col2:
            role_t2 = st.selectbox(
                "Perfil do convidado",
                ["b2b", "b2c", "admin"],
                format_func=lambda r: {
                    "b2b": "Profissional / Salão",
                    "b2c": "Cliente Final",
                    "admin": "Administrador",
                }.get(r, r),
                key="role_t2",
            )
        submitted_t2 = st.form_submit_button(
            "🔗 Gerar link de convite",
            use_container_width=True,
        )

    if submitted_t2:
        if not email_t2 or "@" not in email_t2:
            st.error("⚠️ Informe um e-mail válido para o destinatário.")
        else:
            criado_por = usuario.get("login", "admin")

            # Tenta primeiro via API para persistir no banco
            with st.spinner("Gerando convite..."):
                resultado_api = _criar_convite_via_api(
                    email=email_t2,
                    role=role_t2,
                    token_admin=st.session_state.get("_auth_token"),
                )

            if resultado_api:
                convite = {
                    "token":      resultado_api.get("token", ""),
                    "email":      email_t2,
                    "role":       role_t2,
                    "created_by": criado_por,
                    "signup_url": resultado_api.get("signup_url", ""),
                    "expires_at": resultado_api.get("expires_at", "7 dias"),
                    "email_sent": False,
                    "origem":     "api",
                }
                st.info("📋 Convite criado no banco. Copie e envie manualmente ao convidado.")
            else:
                convite = _gerar_token_local(email_t2, role_t2, criado_por)
                st.warning("⚠️ API indisponível — link gerado localmente (não persistido no banco).")
                st.info("📋 Copie e envie manualmente ao convidado.")

            st.session_state["_convites_gerados"].insert(0, convite)
            _card_link(convite["signup_url"], role_t2, criado_por, convite["origem"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — MONITORAR CONVITES
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    components.section_title("Monitorar convites da sessão")
    st.caption("Exibe todos os convites gerados ou enviados nesta sessão.")

    convites = st.session_state.get("_convites_gerados", [])

    col_clear, _ = st.columns([1, 3])
    with col_clear:
        if st.button("🗑️ Limpar histórico da sessão", use_container_width=True):
            st.session_state["_convites_gerados"] = []
            st.rerun()

    if not convites:
        components.empty_state(
            icon="📨",
            title="Nenhum convite registrado nesta sessão",
            message="Use 'Enviar Convite' para enviar por e-mail ou 'Gerar Convite' para criar um link manual.",
        )
    else:
        total     = len(convites)
        enviados  = sum(1 for c in convites if c.get("email_sent"))
        offline_c = sum(1 for c in convites if c.get("origem") == "offline")
        api_c     = sum(1 for c in convites if c.get("origem") == "api")
        smtp_c    = sum(1 for c in convites if c.get("origem") == "smtp_direto")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total", total)
        m2.metric("E-mail enviado", enviados)
        m3.metric("Via API (banco)", api_c)
        m4.metric("Offline / Fallback", offline_c + smtp_c)

        components.divider()

        for inv in convites:
            email_inv  = inv.get("email", "N/A")
            role_inv   = inv.get("role", "b2b")
            origem_inv = inv.get("origem", "offline")
            email_sent = inv.get("email_sent", False)
            expira     = inv.get("expires_at", "—")
            url_inv    = inv.get("signup_url", "")
            status_env = "✅ Enviado" if email_sent else "📋 Manual"

            label = f"{email_inv}  —  {status_env}  ·  {_badge_role(role_inv)}  ·  {_badge_origem(origem_inv)}"
            with st.expander(label):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**Perfil:** {_badge_role(role_inv)}")
                    st.markdown(f"**E-mail enviado:** {'✅ Sim' if email_sent else '❌ Não'}")
                    st.markdown(f"**Expira em:** {expira}")
                    st.markdown(f"**Origem:** {_badge_origem(origem_inv)}")
                    st.markdown(f"**Criado por:** {inv.get('created_by', '—')}")
                with col_b:
                    st.markdown(f"**Token:** `{inv.get('token', 'N/A')}`")
                    if url_inv:
                        st.markdown("**Link de cadastro:**")
                        st.code(url_inv, language=None)
