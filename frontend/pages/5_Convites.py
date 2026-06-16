"""
5_Convites.py — HIPNUS COSMÉTICOS
====================================
Página de Convites: envio por e-mail e geração de link de convite.

Acesso restrito: admin e super_admin.

Fluxo:
  1. Admin preenche e-mail + nome + mensagem opcional.
  2. Sistema gera token único para o convite.
  3. Duas opções:
     a) Enviar por e-mail via SMTP (Hostinger).
     b) Copiar o link de convite para compartilhar manualmente.
  4. Registro do convite via API (com fallback local em session_state).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import secrets
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

import streamlit as st
from lib import api, ui
from lib.auth import require_auth, sidebar_user_info, sidebar_logout_button
from lib.config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS,
    SMTP_USE_TLS, SMTP_REMETENTE, APP_URL,
)
from lib import components

st.set_page_config(page_title="Convites · HIPNUS", page_icon="📧", layout="wide")
ui.inject_theme()

require_auth(perfis_permitidos=["admin", "super_admin"])

# ─ Sidebar ───────────────────────────────────────────────────────────
ui.brand_header()
sidebar_user_info()
ui.api_status_badge(api.api_online())
ui.sidebar_cart_summary()
sidebar_logout_button()

# ─ Cabeçalho ─────────────────────────────────────────────────────────
components.page_header(
    title="Convites de Parceiros",
    subtitle="Envie convites por e-mail ou gere um link para compartilhar com novos parceiros.",
    kicker="Gestão de parceiros",
)


# ─ Helpers ───────────────────────────────────────────────────────────
def _gerar_token() -> str:
    return secrets.token_urlsafe(24)


def _montar_link(token: str) -> str:
    base = (APP_URL or "https://hipnus-cosmeticos.streamlit.app").rstrip("/")
    return f"{base}/Cadastro_Parceiro?convite={token}"


def _enviar_email_smtp(
    destinatario: str,
    nome: str,
    link: str,
    msg_custom: str,
) -> None:
    """
    Envia o e-mail de convite via SMTP da Hostinger.
    Usa SMTP_REMETENTE como remetente (EMAIL_REMETENTE do Secrets).
    Lança Exception em caso de falha.
    """
    saudacao    = f"Olá, {nome}!" if nome else "Olá!"
    corpo_extra = f"<p>{msg_custom}</p>" if msg_custom else ""
    remetente   = SMTP_REMETENTE or SMTP_USER

    html = f"""
    <html><body style="font-family:Arial,sans-serif;color:#1a1a2e;">
      <div style="max-width:560px;margin:0 auto;padding:32px;
                  background:#f9f9fb;border-radius:12px;">
        <h2 style="color:#7c3aed;">HIPNUS COSMÉTICOS</h2>
        <p>{saudacao}</p>
        <p>Você foi convidado(a) para fazer parte da rede de
           <strong>parceiros e revendedores</strong> da Hipnus Cosméticos.</p>
        {corpo_extra}
        <div style="text-align:center;margin:32px 0;">
          <a href="{link}" style="background:#7c3aed;color:#fff;padding:14px 32px;
             border-radius:8px;text-decoration:none;font-weight:bold;font-size:16px;">
            Aceitar Convite
          </a>
        </div>
        <p style="font-size:12px;color:#888;">Ou copie e cole este link no navegador:</p>
        <p style="font-size:12px;color:#7c3aed;word-break:break-all;">{link}</p>
        <hr style="border:none;border-top:1px solid #e0e0e0;margin:24px 0;">
        <p style="font-size:11px;color:#aaa;">
          HIPNUS COSMÉTICOS &copy; 2026 &mdash; Plataforma exclusiva da marca.
        </p>
      </div>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Convite Hipnus Cosméticos — Seja um parceiro!"
    msg["From"]    = remetente
    msg["To"]      = destinatario
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        if SMTP_USE_TLS:
            server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(remetente, destinatario, msg.as_string())


# ─ Formulário ────────────────────────────────────────────────────────
col_form, col_info = st.columns([2, 1])

with col_form:
    with st.form("form_convite", clear_on_submit=False):
        email_dest = st.text_input("📧 E-mail do parceiro *", placeholder="parceiro@exemplo.com")
        nome_dest  = st.text_input("👤 Nome do parceiro (opcional)", placeholder="Ex.: Salão Beleza Total")
        mensagem   = st.text_area(
            "💬 Mensagem personalizada (opcional)",
            placeholder="Olá! Convidamos você a fazer parte da rede de parceiros Hipnus...",
            height=100,
        )
        modo = st.radio(
            "Como deseja enviar?",
            options=["Enviar por e-mail", "Gerar link para copiar"],
            horizontal=True,
        )
        enviar = st.form_submit_button("📨 Gerar Convite", type="primary", use_container_width=True)

with col_info:
    st.markdown("")
    smtp_configurado = bool(SMTP_USER and SMTP_PASS)
    if smtp_configurado:
        components.feedback_inline("SMTP configurado — envio de e-mail ativo.", kind="success")
    else:
        components.feedback_inline(
            "SMTP não configurado. Use o modo Gerar link para compartilhar manualmente.",
            kind="warning",
        )
    st.markdown("")
    with st.popover("💡 Como funciona?", use_container_width=True):
        st.markdown(
            "- O sistema gera um **link único** para cada convite.\n"
            "- Envie por **e-mail automático** ou **copie o link** para WhatsApp, Instagram, etc.\n"
            "- O parceiro clica e já acessa o cadastro com o convite pré-preenchido."
        )


# ─ Processamento ─────────────────────────────────────────────────────
if enviar:
    erros = []
    if not email_dest.strip() or "@" not in email_dest:
        erros.append("E-mail inválido. Verifique o campo e-mail.")

    if erros:
        for e in erros:
            components.feedback_inline(e, kind="danger")
    else:
        token = _gerar_token()
        link  = _montar_link(token)
        nome  = nome_dest.strip() or ""
        msg_c = mensagem.strip() or ""

        # Registra na API (best-effort)
        registrado_api = False
        try:
            api.send_invite(
                email=email_dest.strip(),
                nome=nome or None,
                mensagem=msg_c or None,
                token=token,
            )
            registrado_api = True
        except Exception:
            if "_convites_locais" not in st.session_state:
                st.session_state["_convites_locais"] = []
            st.session_state["_convites_locais"].append({
                "email": email_dest.strip(),
                "nome": nome,
                "token": token,
                "link": link,
                "created_at": datetime.now().isoformat(),
                "accepted": False,
                "_local": True,
            })

        # ─ Modo: enviar por e-mail ────────────────────────────────────
        if modo == "Enviar por e-mail":
            if not (SMTP_USER and SMTP_PASS):
                components.feedback_inline(
                    "SMTP não configurado. Copie o link abaixo e envie manualmente:",
                    kind="warning",
                )
                st.code(link, language=None)
            else:
                smtp_ok  = False
                smtp_err = ""
                with st.spinner("Enviando e-mail..."):
                    try:
                        _enviar_email_smtp(
                            destinatario=email_dest.strip(),
                            nome=nome,
                            link=link,
                            msg_custom=msg_c,
                        )
                        smtp_ok = True
                    except Exception as exc:
                        smtp_err = str(exc)

                if smtp_ok:
                    components.feedback_inline(
                        f"Convite enviado por e-mail para {email_dest.strip()}!",
                        kind="success",
                    )
                    if not registrado_api:
                        st.caption("📦 Registrado localmente (API offline).")
                else:
                    components.feedback_inline(
                        "Não foi possível enviar o e-mail. Copie o link abaixo e envie manualmente:",
                        kind="warning",
                    )
                    st.code(link, language=None)
                    if smtp_err:
                        with st.popover("🔍 Detalhes do erro SMTP", use_container_width=False):
                            st.text(smtp_err)

        # ─ Modo: gerar link ───────────────────────────────────────────
        else:
            components.feedback_inline(
                f"Link de convite gerado para {email_dest.strip()}!",
                kind="success",
            )
            st.markdown("**Copie o link abaixo e envie pelo canal de sua preferência:**")
            st.code(link, language=None)
            st.caption("📤 Compartilhe via WhatsApp, Instagram, e-mail manual ou qualquer outro canal.")
            if not registrado_api:
                st.caption("📦 Registrado localmente (API offline).")


# ─ Lista de convites ─────────────────────────────────────────────────
components.divider()
components.section_title("Convites enviados")

convites_api    = api.list_invites()
convites_locais = st.session_state.get("_convites_locais", [])
todos = convites_api + [
    c for c in convites_locais
    if not any(
        x.get("email") == c["email"] and x.get("token") == c.get("token")
        for x in convites_api
    )
]

if not todos:
    components.empty_state(
        icon="📧",
        title="Nenhum convite enviado ainda",
        message="Use o formulário acima para convidar um parceiro.",
    )
else:
    for c in sorted(todos, key=lambda x: x.get("created_at", ""), reverse=True):
        status_icon  = "✅" if c.get("accepted") else "⏳"
        local_tag    = " · *local*" if c.get("_local") else ""
        link_convite = c.get("link") or _montar_link(c.get("token", ""))
        data         = (c.get("created_at") or "")[:10] or "—"
        status_txt   = "Aceito" if c.get("accepted") else "Pendente"

        with st.popover(
            f"{status_icon} {c.get('email', '?')} — {data}{local_tag}",
            use_container_width=False,
        ):
            st.markdown(f"**Status:** {status_txt} {status_icon}")
            if c.get("nome"):
                st.markdown(f"**Nome:** {c['nome']}")
            st.markdown("**Link do convite:**")
            st.code(link_convite, language=None)
