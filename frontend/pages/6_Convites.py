"""
6_Convites.py — HIPNUS COSMÉTICOS
====================================
Gerenciamento de convites de cadastro para parceiros e distribuidores.

Estrutura em 3 abas:
  tab1 — Enviar Convite  : gera token + envia e-mail DIRETAMENTE via SMTP
                           usando as credenciais do bloco [email] dos Streamlit Secrets.
                           NÃO depende de FastAPI nem de backend externo.
  tab2 — Gerar Convite   : gera token/link offline para envio manual.
  tab3 — Monitorar       : lista e monitora todos os convites gerados na sessão.

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
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

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


# ─── Helpers ─────────────────────────────────────────────────────────────────
def _gerar_token_convite(email: str, role: str, criado_por: str) -> dict:
    """
    Gera token UUID4 hex e monta o link de cadastro com APP_URL.
    Usado tanto na Tab1 (com envio SMTP) quanto na Tab2 (offline).
    """
    token      = uuid.uuid4().hex
    signup_url = f"{APP_URL}/Cadastro_Parceiro?invite={token}"
    expires_at = datetime.utcnow() + timedelta(days=7)
    return {
        "token":      token,
        "email":      email,
        "role":       role,
        "created_by": criado_por,
        "signup_url": signup_url,
        "expires_at": expires_at.strftime("%d/%m/%Y %H:%M") + " UTC",
        "email_sent": False,
        "origem":     "smtp_direto",
    }


def _enviar_email_smtp(destinatario: str, signup_url: str, role: str, token: str) -> tuple[bool, str]:
    """
    Envia e-mail de convite diretamente via SMTP usando as credenciais
    configuradas no bloco [email] dos Streamlit Secrets.

    Suporta TLS (STARTTLS na porta 587) e SSL (porta 465).
    Retorna (sucesso: bool, mensagem: str).

    Parâmetros:
      destinatario : e-mail do convidado
      signup_url   : link de cadastro com token
      role         : perfil do convidado (b2b, b2c, admin)
      token        : token UUID do convite

    Efeitos colaterais:
      Envia e-mail real via SMTP Hostinger.
    """
    if not SMTP_USER or not SMTP_PASS:
        return False, (
            "Credenciais SMTP não configuradas. "
            "Verifique EMAIL_USERNAME e EMAIL_PASSWORD no bloco [email] dos Streamlit Secrets."
        )

    role_label = {"b2b": "Profissional / Salão", "b2c": "Cliente Final", "admin": "Administrador"}.get(role, role)
    expira     = (datetime.utcnow() + timedelta(days=7)).strftime("%d/%m/%Y")

    # ── Corpo HTML do e-mail ──────────────────────────────────────────────────
    html_body = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head><meta charset="UTF-8"></head>
    <body style="margin:0;padding:0;background:#F6F4FB;font-family:Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#F6F4FB;padding:32px 0;">
        <tr><td align="center">
          <table width="560" cellpadding="0" cellspacing="0"
                 style="background:#fff;border-radius:16px;overflow:hidden;
                        box-shadow:0 2px 16px rgba(124,58,237,.10);">
            <!-- Header -->
            <tr>
              <td style="background:linear-gradient(135deg,#7C3AED,#5B21B6);
                         padding:32px 40px;text-align:center;">
                <h1 style="color:#fff;margin:0;font-size:22px;letter-spacing:1px;">
                  HIPNUS COSMÉTICOS
                </h1>
                <p style="color:#e9d5ff;margin:6px 0 0;font-size:13px;">
                  Tratamento capilar profissional, direto da fonte.
                </p>
              </td>
            </tr>
            <!-- Body -->
            <tr>
              <td style="padding:36px 40px;">
                <h2 style="color:#1A1430;font-size:18px;margin:0 0 12px;">Você foi convidado! 🎉</h2>
                <p style="color:#4B4565;font-size:14px;line-height:1.6;margin:0 0 20px;">
                  Você recebeu um convite exclusivo para se cadastrar na plataforma
                  <strong>HIPNUS COSMÉTICOS</strong> como <strong>{role_label}</strong>.
                </p>
                <p style="color:#4B4565;font-size:14px;line-height:1.6;margin:0 0 28px;">
                  Clique no botão abaixo para criar sua conta. O convite é válido até
                  <strong>{expira}</strong>.
                </p>
                <!-- CTA Button -->
                <table cellpadding="0" cellspacing="0" width="100%">
                  <tr>
                    <td align="center" style="padding:0 0 28px;">
                      <a href="{signup_url}"
                         style="display:inline-block;background:#7C3AED;color:#fff;
                                text-decoration:none;font-size:15px;font-weight:700;
                                padding:14px 36px;border-radius:8px;
                                letter-spacing:.4px;">
                        ✅ Criar minha conta
                      </a>
                    </td>
                  </tr>
                </table>
                <!-- Link alternativo -->
                <p style="color:#6B6580;font-size:12px;margin:0 0 8px;">Ou copie e cole este link no navegador:</p>
                <p style="background:#F6F4FB;border:1px solid #E7E3F2;border-radius:6px;
                           padding:10px 14px;font-family:monospace;font-size:12px;
                           color:#7C3AED;word-break:break-all;margin:0 0 24px;">
                  {signup_url}
                </p>
                <hr style="border:none;border-top:1px solid #E7E3F2;margin:0 0 20px;">
                <p style="color:#9CA3AF;font-size:11px;margin:0;">
                  Se você não solicitou este convite, ignore este e-mail.<br>
                  Token: <code>{token[:8]}…</code>
                </p>
              </td>
            </tr>
            <!-- Footer -->
            <tr>
              <td style="background:#F6F4FB;padding:18px 40px;text-align:center;">
                <p style="color:#9CA3AF;font-size:11px;margin:0;">
                  HIPNUS COSMÉTICOS · (31) 98321-3343 · www.hipnuscosmeticos.com.br
                </p>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🎉 Seu convite para a plataforma HIPNUS COSMÉTICOS"
    msg["From"]    = f"HIPNUS COSMÉTICOS <{SMTP_REMETENTE}>"
    msg["To"]      = destinatario
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if SMTP_USE_SSL:
            # Porta 465 — SSL direto
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(SMTP_REMETENTE, destinatario, msg.as_string())
        else:
            # Porta 587 — STARTTLS (padrão Hostinger)
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
                server.ehlo()
                if SMTP_USE_TLS:
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(SMTP_REMETENTE, destinatario, msg.as_string())

        return True, "E-mail enviado com sucesso."

    except smtplib.SMTPAuthenticationError:
        return False, (
            "Falha de autenticação SMTP. Verifique EMAIL_USERNAME e EMAIL_PASSWORD nos Secrets."
        )
    except smtplib.SMTPConnectError:
        return False, f"Não foi possível conectar ao servidor SMTP {SMTP_HOST}:{SMTP_PORT}."
    except smtplib.SMTPException as exc:
        return False, f"Erro SMTP: {exc}"
    except Exception as exc:
        return False, f"Erro inesperado ao enviar e-mail: {exc}"


def _badge_role(role: str) -> str:
    return {"b2b": "🎤 Profissional", "b2c": "👤 Cliente", "admin": "🛡️ Admin"}.get(role, role)


def _badge_origem(origem: str) -> str:
    mapa = {"smtp_direto": "🟢 SMTP Direto", "offline": "🟡 Offline", "api": "🔵 API"}
    return mapa.get(origem, origem)


def _card_link(signup_url: str, role: str, criado_por: str, origem: str) -> None:
    """Renderiza card visual com link de cadastro copiável."""
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
    """Exibe status da configuração SMTP no sidebar ou inline."""
    if not SMTP_USER or not SMTP_PASS:
        st.html(f"""
        <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:10px;
                    padding:12px 16px;font-size:.82rem;color:#92400e;margin-bottom:12px;">
            <strong>⚙️ SMTP não configurado.</strong><br>
            Adicione no <code>.streamlit/secrets.toml</code>:<br><br>
            <code>[email]</code><br>
            <code>EMAIL_HOST = "smtp.hostinger.com"</code><br>
            <code>EMAIL_PORT = "587"</code><br>
            <code>EMAIL_USERNAME = "seu@email.com"</code><br>
            <code>EMAIL_PASSWORD = "sua_senha"</code><br>
            <code>EMAIL_USE_TLS = "true"</code><br>
            <code>EMAIL_REMETENTE = "seu@email.com"</code>
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

# ─── Tabs ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📨 Enviar Convite", "🔗 Gerar Convite", "📋 Monitorar Convites"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ENVIAR CONVITE (SMTP direto, sem FastAPI)
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    components.section_title("Enviar convite por e-mail")
    st.caption(
        "Gera o token de convite e envia o e-mail diretamente via SMTP Hostinger "
        "configurado nos Streamlit Secrets — sem depender de backend externo."
    )

    _aviso_smtp_config()

    with st.form("form_enviar_convite", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            email_t1 = st.text_input(
                "E-mail do destinatário",
                placeholder="parceiro@email.com",
            )
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
            convite    = _gerar_token_convite(email_t1, role_t1, criado_por)

            with st.spinner(f"Enviando e-mail para {email_t1} via {SMTP_HOST}..."):
                ok, msg_smtp = _enviar_email_smtp(
                    destinatario=email_t1,
                    signup_url=convite["signup_url"],
                    role=role_t1,
                    token=convite["token"],
                )

            convite["email_sent"] = ok
            st.session_state["_convites_gerados"].insert(0, convite)

            if ok:
                st.success(f"✅ Convite enviado por e-mail para **{email_t1}**!")
                _card_link(convite["signup_url"], role_t1, criado_por, "smtp_direto")
            else:
                st.error(f"❌ Falha ao enviar e-mail.\n\n**Detalhe:** {msg_smtp}")
                st.info(
                    "💡 O link de convite foi gerado mesmo assim. "
                    "Copie abaixo e envie manualmente ao convidado."
                )
                _card_link(convite["signup_url"], role_t1, criado_por, "offline")


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
            convite    = _gerar_token_convite(email_t2, role_t2, criado_por)
            convite["origem"] = "offline"
            st.session_state["_convites_gerados"].insert(0, convite)

            st.info("📋 Link gerado. Copie e envie manualmente ao convidado.")
            _card_link(convite["signup_url"], role_t2, criado_por, "offline")


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
        smtp_c    = sum(1 for c in convites if c.get("origem") == "smtp_direto")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total", total)
        m2.metric("E-mail enviado", enviados)
        m3.metric("SMTP Direto", smtp_c)
        m4.metric("Offline / Manual", offline_c)

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
