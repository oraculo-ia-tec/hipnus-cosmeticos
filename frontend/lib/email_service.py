"""
email_service.py — HIPNUS COSMÉTICOS
====================================
Skill: 📧 Notificações por E-mail

Envia e-mails transacionais via SMTP Hostinger já configurado no ambiente.
Também expõe helpers de diagnóstico para a tela de Configurações.
"""
from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Iterable

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.hostinger.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "no-reply@hipnuscosmeticos.com.br")


def smtp_status() -> dict:
    """Retorna status da configuração SMTP sem expor segredos."""
    return {
        "host": SMTP_HOST,
        "port": SMTP_PORT,
        "user_configured": bool(SMTP_USER),
        "password_configured": bool(SMTP_PASSWORD),
        "from_email": SMTP_FROM,
        "ready": bool(SMTP_HOST and SMTP_PORT and SMTP_USER and SMTP_PASSWORD and SMTP_FROM),
    }


def _build_message(
    to_email: str | Iterable[str],
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to_email if isinstance(to_email, str) else ", ".join(to_email)
    msg.set_content(text_body or "Seu cliente de e-mail não suporta HTML. Abra a versão web.")
    msg.add_alternative(html_body, subtype="html")
    return msg


def send_email(
    to_email: str | Iterable[str],
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> tuple[bool, str]:
    """Envia e-mail via SMTP SSL (Hostinger porta 465)."""
    status = smtp_status()
    if not status["ready"]:
        return False, "SMTP incompleto. Configure SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD e SMTP_FROM."

    try:
        msg = _build_message(to_email=to_email, subject=subject, html_body=html_body, text_body=text_body)
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=20) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return True, "E-mail enviado com sucesso."
    except Exception as exc:
        return False, f"Falha ao enviar e-mail: {exc}"


def send_test_email(to_email: str) -> tuple[bool, str]:
    """Envia um e-mail de teste com layout padrão Hipnus."""
    html = f"""
    <div style="font-family:Inter,Segoe UI,sans-serif;background:#f8f7fc;padding:32px;">
      <div style="max-width:620px;margin:0 auto;background:#ffffff;border:1px solid #e5e0f5;border-radius:18px;overflow:hidden;">
        <div style="background:linear-gradient(135deg,#7c3aed 0%,#5b21b6 100%);padding:28px 32px;color:#fff;">
          <div style="font-size:12px;letter-spacing:1.4px;text-transform:uppercase;opacity:.85;font-weight:700;">HIPNUS COSMÉTICOS</div>
          <h1 style="margin:10px 0 0;font-size:24px;line-height:1.2;">Teste de SMTP concluído</h1>
        </div>
        <div style="padding:28px 32px;color:#1a1430;">
          <p style="font-size:15px;line-height:1.7;margin:0 0 16px;">Este é um envio de teste da <strong>Skill de Notificações por E-mail</strong>.</p>
          <p style="font-size:15px;line-height:1.7;margin:0 0 16px;">Se você recebeu esta mensagem, o SMTP Hostinger está ativo e pronto para disparos transacionais no projeto.</p>
          <div style="background:#f3f0ff;border:1px solid #e9d5ff;border-radius:14px;padding:14px 16px;font-size:14px;color:#5b21b6;">
            Próximos usos: convite de parceiro, confirmação de pedido, status de pagamento e alertas internos.
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
