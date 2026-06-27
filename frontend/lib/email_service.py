"""
email_service.py — HIPNUS COSMÉTICOS
====================================
Skill: 📧 Notificações por E-mail

Serviço centralizado de e-mail via SMTP Hostinger (porta 465 / SSL).
Exporta:
  - smtp_status()          — diagnóstico seguro do ambiente
  - send_email()           — envio genérico HTML
  - send_test_email()      — e-mail de teste com layout Hipnus
  - send_invite_email()    — convite de parceiro com link de cadastro
"""
from __future__ import annotations

import os
import smtplib
import ssl
from datetime import datetime, timedelta
from email.header import Header
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate
from typing import Iterable

SMTP_HOST     = os.getenv("SMTP_HOST",     "smtp.hostinger.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER     = os.getenv("SMTP_USER",     "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM     = os.getenv("SMTP_FROM",     "no-reply@hipnuscosmeticos.com.br")

INVITE_EXPIRY_DAYS = 7


# ─── Diagnóstico ──────────────────────────────────────────────────────────
def smtp_status() -> dict:
    """Retorna status da configuração SMTP sem expor segredos."""
    return {
        "host":                 SMTP_HOST,
        "port":                 SMTP_PORT,
        "user_configured":      bool(SMTP_USER),
        "password_configured":  bool(SMTP_PASSWORD),
        "from_email":           SMTP_FROM,
        "ready":                bool(SMTP_HOST and SMTP_PORT and SMTP_USER and SMTP_PASSWORD and SMTP_FROM),
    }


# ─── Engine de envio interno ─────────────────────────────────────────────────
def _send_via_ssl(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str,
) -> tuple[bool, str]:
    """Envia usando SMTP_SSL (porta 465, padrão Hostinger)."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = Header(subject, "utf-8").encode()
        msg["From"]    = formataddr(("HIPNUS COSMÉTICOS", SMTP_FROM))
        msg["To"]      = to_email
        msg["Date"]    = formatdate(localtime=False)
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html",  "utf-8"))
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=20) as s:
            s.login(SMTP_USER, SMTP_PASSWORD)
            s.sendmail(SMTP_FROM, to_email, msg.as_string())
        return True, "E-mail enviado com sucesso."
    except smtplib.SMTPAuthenticationError:
        return False, "Falha de autenticação SMTP. Verifique SMTP_USER e SMTP_PASSWORD."
    except Exception as exc:
        return False, f"Falha ao enviar e-mail: {exc}"


# ─── API pública ───────────────────────────────────────────────────────────────
def send_email(
    to_email: str | Iterable[str],
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> tuple[bool, str]:
    """Envio genérico. Aceita um ou múltiplos destinatários."""
    status = smtp_status()
    if not status["ready"]:
        return False, "SMTP incompleto. Configure SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD e SMTP_FROM."
    recipients = [to_email] if isinstance(to_email, str) else list(to_email)
    errors = []
    for recipient in recipients:
        ok, msg = _send_via_ssl(
            to_email=recipient,
            subject=subject,
            html_body=html_body,
            text_body=text_body or "Seu cliente de e-mail não suporta HTML.",
        )
        if not ok:
            errors.append(f"{recipient}: {msg}")
    if errors:
        return False, " | ".join(errors)
    return True, "E-mail(s) enviado(s) com sucesso."


def send_test_email(to_email: str) -> tuple[bool, str]:
    """E-mail de teste com layout padrão Hipnus."""
    html = f"""
    <div style="font-family:Inter,Segoe UI,sans-serif;background:#f8f7fc;padding:32px;">
      <div style="max-width:620px;margin:0 auto;background:#fff;border:1px solid #e5e0f5;
                  border-radius:18px;overflow:hidden;">
        <div style="background:linear-gradient(135deg,#7c3aed 0%,#5b21b6 100%);
                    padding:28px 32px;color:#fff;">
          <div style="font-size:12px;letter-spacing:1.4px;text-transform:uppercase;
                      opacity:.85;font-weight:700;">HIPNUS COSMÉTICOS</div>
          <h1 style="margin:10px 0 0;font-size:24px;line-height:1.2;">
            Teste de SMTP concluído ✅
          </h1>
        </div>
        <div style="padding:28px 32px;color:#1a1430;">
          <p style="font-size:15px;line-height:1.7;margin:0 0 16px;">
            Este é um envio de teste da <strong>Skill de Notificações por E-mail</strong>.
          </p>
          <p style="font-size:15px;line-height:1.7;margin:0 0 16px;">
            Se você recebeu esta mensagem, o SMTP Hostinger está ativo e pronto
            para disparos transacionais no projeto.
          </p>
          <div style="background:#f3f0ff;border:1px solid #e9d5ff;border-radius:14px;
                      padding:14px 16px;font-size:14px;color:#5b21b6;">
            Próximos usos: convite de parceiro, confirmação de pedido,
            status de pagamento e alertas internos.
          </div>
        </div>
      </div>
    </div>
    """
    text = (
        "HIPNUS COSMÉTICOS\n\n"
        "Teste de SMTP concluído.\n"
        "Se você recebeu esta mensagem, o SMTP Hostinger está ativo e pronto para uso."
    )
    return send_email(
        to_email=to_email,
        subject="HIPNUS — Teste de SMTP concluído",
        html_body=html,
        text_body=text,
    )


def send_invite_email(
    destinatario: str,
    signup_url: str,
    role: str,
) -> tuple[bool, str]:
    """
    Envia o convite de parceiro com template visual completo.
    Centraliza o disparo que antes existia como função local em 6_Convites.py.
    """
    status = smtp_status()
    if not status["ready"]:
        return False, "Credenciais SMTP não configuradas."

    role_label = {
        "b2b":   "Profissional / Salão",
        "b2c":   "Cliente Final",
        "admin": "Administrador",
    }.get(role, role)
    expira = (datetime.utcnow() + timedelta(days=INVITE_EXPIRY_DAYS)).strftime("%d/%m/%Y")

    html_body = f"""\
<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#F6F4FB;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" border="0"
       style="background:#F6F4FB;padding:32px 0;">
<tr><td align="center">
  <table width="560" cellpadding="0" cellspacing="0" border="0"
         style="background:#fff;border-radius:16px;border:1px solid #E7E3F2;">
    <tr><td style="background:#7C3AED;padding:28px 40px;text-align:center;
                   border-radius:16px 16px 0 0;">
      <div style="font-size:1.3rem;font-weight:800;color:#fff;">HIPNUS COSM&#201;TICOS</div>
      <div style="font-size:.72rem;color:rgba(255,255,255,.75);letter-spacing:2px;
                  text-transform:uppercase;margin-top:4px;">Convite de Acesso</div>
    </td></tr>
    <tr><td style="padding:32px 40px;">
      <p style="font-size:1rem;color:#1A1430;margin:0 0 20px;line-height:1.6;">
        Voc&#234; recebeu um convite exclusivo como
        <strong>{role_label}</strong>.
        V&#225;lido at&#233; <strong>{expira}</strong>.
      </p>
      <table cellpadding="0" cellspacing="0" border="0" width="100%">
        <tr><td align="center" style="padding:0 0 20px;">
          <a href="{signup_url}"
             style="display:inline-block;background:#7C3AED;color:#fff;
                    text-decoration:none;font-size:15px;font-weight:bold;
                    padding:14px 40px;border-radius:10px;">
            Concluir meu cadastro
          </a>
        </td></tr>
      </table>
      <p style="font-size:.8rem;color:#6B6580;margin:0 0 8px;">
        Ou copie e cole o link no navegador:
      </p>
      <div style="background:#F6F4FB;border:1px solid #E7E3F2;border-radius:6px;
                  padding:10px 14px;">
        <span style="font-family:monospace;font-size:12px;color:#7C3AED;
                     word-break:break-all;">{signup_url}</span>
      </div>
    </td></tr>
    <tr><td style="background:#F6F4FB;padding:14px 40px;text-align:center;
                   border-radius:0 0 16px 16px;border-top:1px solid #E7E3F2;">
      <p style="color:#9CA3AF;font-size:11px;margin:0;">HIPNUS COSM&#201;TICOS &copy; 2026</p>
    </td></tr>
  </table>
</td></tr></table>
</body></html>"""

    text_body = (
        f"Você foi convidado para HIPNUS COSMÉTICOS!\n\n"
        f"Perfil: {role_label}\nVálido até: {expira}\n\n"
        f"Link de cadastro:\n{signup_url}\n"
    )

    return _send_via_ssl(
        to_email=destinatario,
        subject="Seu convite para HIPNUS COSMÉTICOS",
        html_body=html_body,
        text_body=text_body,
    )
