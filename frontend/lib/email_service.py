"""
email_service.py — HIPNUS COSMÉTICOS
====================================
Skill: 📧 Notificações por E-mail

Lê credenciais de st.secrets["email"] (Streamlit Cloud) com fallback os.getenv.
Nomes das chaves: EMAIL_HOST, EMAIL_PORT, EMAIL_USERNAME, EMAIL_PASSWORD,
                  EMAIL_USE_TLS, EMAIL_USE_SSL, EMAIL_REMETENTE
"""
from __future__ import annotations

import os
import smtplib
import ssl
from datetime import datetime, timedelta
from decimal import Decimal
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate
from typing import Iterable


def _secret(key: str, default: str = "") -> str:
    """
    Lê credencial tentando (em ordem):
      1. st.secrets["email"][key]  ← seção [email] no secrets.toml
      2. st.secrets[key]           ← raiz do secrets.toml
      3. os.getenv(key, default)   ← variável de ambiente
    """
    try:
        import streamlit as st
        try:
            val = st.secrets["email"][key]
            if val is not None and str(val).strip():
                return str(val).strip()
        except Exception:
            pass
        try:
            val = st.secrets[key]
            if val is not None and str(val).strip():
                return str(val).strip()
        except Exception:
            pass
    except Exception:
        pass
    return os.getenv(key, default)


def _get_smtp_config() -> dict:
    """Retorna configurações SMTP lidas dinamicamente a cada chamada."""
    use_tls = _secret("EMAIL_USE_TLS", "true").lower() == "true"
    use_ssl = _secret("EMAIL_USE_SSL", "false").lower() == "true"
    return {
        "host":      _secret("EMAIL_HOST",     "smtp.hostinger.com"),
        "port":      int(_secret("EMAIL_PORT", "587")),
        "user":      _secret("EMAIL_USERNAME", ""),
        "password":  _secret("EMAIL_PASSWORD", ""),
        "from":      _secret("EMAIL_REMETENTE", "") or _secret("EMAIL_USERNAME", "no-reply@hipnuscosmeticos.com.br"),
        "use_tls":   use_tls,
        "use_ssl":   use_ssl,
    }


INVITE_EXPIRY_DAYS = 7


# ─── Diagnóstico ───────────────────────────────────────────────────────
def smtp_status() -> dict:
    """Retorna status da configuração SMTP sem expor segredos."""
    cfg = _get_smtp_config()
    return {
        "host":                cfg["host"],
        "port":                cfg["port"],
        "user_configured":     bool(cfg["user"]),
        "password_configured": bool(cfg["password"]),
        "from_email":          cfg["from"],
        "use_tls":             cfg["use_tls"],
        "use_ssl":             cfg["use_ssl"],
        "ready":               bool(cfg["host"] and cfg["port"] and cfg["user"] and cfg["password"]),
    }


# ─── Engine de envio ────────────────────────────────────────────────────────
def _send(to_email: str, subject: str, html_body: str, text_body: str) -> tuple[bool, str]:
    """Envia e-mail via SMTP_SSL (porta 465) ou STARTTLS (porta 587)."""
    cfg = _get_smtp_config()
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = Header(subject, "utf-8").encode()
        msg["From"]    = formataddr(("HIPNUS COSMÉTICOS", cfg["from"]))
        msg["To"]      = to_email
        msg["Date"]    = formatdate(localtime=False)
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html",  "utf-8"))

        context = ssl.create_default_context()

        if cfg["use_ssl"]:
            # Porta 465 — SMTP_SSL
            with smtplib.SMTP_SSL(cfg["host"], cfg["port"], context=context, timeout=20) as s:
                s.login(cfg["user"], cfg["password"])
                s.sendmail(cfg["from"], to_email, msg.as_string())
        else:
            # Porta 587 — STARTTLS (padrão Hostinger)
            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=20) as s:
                s.ehlo()
                if cfg["use_tls"]:
                    s.starttls(context=context)
                    s.ehlo()
                s.login(cfg["user"], cfg["password"])
                s.sendmail(cfg["from"], to_email, msg.as_string())

        return True, "E-mail enviado com sucesso."
    except smtplib.SMTPAuthenticationError:
        return False, "Falha de autenticação SMTP. Verifique EMAIL_USERNAME e EMAIL_PASSWORD."
    except Exception as exc:
        return False, f"Falha ao enviar e-mail: {exc}"


# Alias para compatibilidade interna
_send_via_ssl = _send


# ─── API pública ────────────────────────────────────────────────────────────────────────
def send_email(
    to_email: str | Iterable[str],
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> tuple[bool, str]:
    """Envio genérico. Aceita um ou múltiplos destinatários."""
    if not smtp_status()["ready"]:
        return False, "SMTP incompleto. Configure EMAIL_HOST, EMAIL_PORT, EMAIL_USERNAME, EMAIL_PASSWORD nos Secrets."
    recipients = [to_email] if isinstance(to_email, str) else list(to_email)
    errors = []
    for recipient in recipients:
        ok, msg = _send(recipient, subject, html_body, text_body or "Seu cliente de e-mail não suporta HTML.")
        if not ok:
            errors.append(f"{recipient}: {msg}")
    if errors:
        return False, " | ".join(errors)
    return True, "E-mail(s) enviado(s) com sucesso."


def send_test_email(to_email: str) -> tuple[bool, str]:
    """E-mail de teste com layout padrão Hipnus."""
    html = """
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
            Se você recebeu esta mensagem, o SMTP Hostinger está ativo e pronto.
          </p>
        </div>
      </div>
    </div>
    """
    return send_email(to_email, "HIPNUS — Teste de SMTP", html)


def send_invite_email(destinatario: str, signup_url: str, role: str) -> tuple[bool, str]:
    """Envia convite de parceiro com template visual."""
    if not smtp_status()["ready"]:
        return False, "Credenciais SMTP não configuradas."

    role_label = {"b2b": "Profissional / Salão", "b2c": "Cliente Final", "admin": "Administrador"}.get(role, role)
    expira = (datetime.utcnow() + timedelta(days=INVITE_EXPIRY_DAYS)).strftime("%d/%m/%Y")

    html_body = f"""\
<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#F6F4FB;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F6F4FB;padding:32px 0;">
<tr><td align="center">
  <table width="560" cellpadding="0" cellspacing="0"
         style="background:#fff;border-radius:16px;border:1px solid #E7E3F2;">
    <tr><td style="background:#7C3AED;padding:28px 40px;text-align:center;border-radius:16px 16px 0 0;">
      <div style="font-size:1.3rem;font-weight:800;color:#fff;">HIPNUS COSM&#201;TICOS</div>
      <div style="font-size:.72rem;color:rgba(255,255,255,.75);letter-spacing:2px;
                  text-transform:uppercase;margin-top:4px;">Convite de Acesso</div>
    </td></tr>
    <tr><td style="padding:32px 40px;">
      <p style="font-size:1rem;color:#1A1430;margin:0 0 20px;line-height:1.6;">
        Voc&#234; recebeu um convite como <strong>{role_label}</strong>. V&#225;lido at&#233; <strong>{expira}</strong>.
      </p>
      <table cellpadding="0" cellspacing="0" width="100%">
        <tr><td align="center" style="padding:0 0 20px;">
          <a href="{signup_url}"
             style="display:inline-block;background:#7C3AED;color:#fff;
                    text-decoration:none;font-size:15px;font-weight:bold;
                    padding:14px 40px;border-radius:10px;">
            Concluir meu cadastro
          </a>
        </td></tr>
      </table>
      <div style="background:#F6F4FB;border:1px solid #E7E3F2;border-radius:6px;padding:10px 14px;">
        <span style="font-family:monospace;font-size:12px;color:#7C3AED;word-break:break-all;">{signup_url}</span>
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
        f"Perfil: {role_label}\nVálido até: {expira}\n\nLink:\n{signup_url}\n"
    )
    return _send(destinatario, "Seu convite para HIPNUS COSMÉTICOS", html_body, text_body)


# ─── Skill #3 — Confirmação de pedido ──────────────────────────────────────────────────────
def _brl(v) -> str:
    try:
        val = Decimal(str(v))
    except Exception:
        val = Decimal("0")
    s = f"{val:,.2f}"
    return f"R$ {s}".replace(",", "X").replace(".", ",").replace("X", ".")


def send_order_confirmation_email(
    to_email: str,
    customer_name: str,
    billing_type: str,
    resultado: dict,
    itens: list[dict],
) -> tuple[bool, str]:
    if not smtp_status()["ready"]:
        return False, "SMTP não configurado."

    total            = resultado.get("totais", {}).get("total", 0)
    external_ref     = resultado.get("external_ref", "")
    payment_id       = resultado.get("payment_id", "")
    invoice_url      = resultado.get("invoice_url", "")
    status_pagamento = resultado.get("status", "")
    metodo_label     = {"PIX": "PIX", "BOLETO": "Boleto", "CREDIT_CARD": "Cartão"}.get(billing_type, billing_type)

    linhas_html = "".join(
        f"<tr>"
        f"<td style='padding:10px 12px;border-bottom:1px solid #eee;'>{item['name']}</td>"
        f"<td style='padding:10px 12px;border-bottom:1px solid #eee;text-align:center;'>{item['qty']}</td>"
        f"<td style='padding:10px 12px;border-bottom:1px solid #eee;text-align:right;'>"
        f"{_brl(Decimal(str(item['price'])) * Decimal(str(item['qty'])))}</td>"
        f"</tr>"
        for item in itens
    )
    cta = (
        f"<a href='{invoice_url}' style='display:inline-block;background:#7C3AED;color:#fff;"
        f"text-decoration:none;font-size:15px;font-weight:bold;padding:14px 28px;border-radius:10px;'>"
        f"Abrir pagamento</a>" if invoice_url else ""
    )
    html_body = f"""
    <div style='font-family:Inter,sans-serif;background:#f8f7fc;padding:32px;'>
      <div style='max-width:680px;margin:0 auto;background:#fff;border:1px solid #e5e0f5;border-radius:18px;overflow:hidden;'>
        <div style='background:linear-gradient(135deg,#7c3aed,#5b21b6);padding:28px 32px;color:#fff;'>
          <div style='font-size:12px;letter-spacing:1.4px;text-transform:uppercase;opacity:.85;font-weight:700;'>HIPNUS COSMÉTICOS</div>
          <h1 style='margin:10px 0 0;font-size:24px;'>Pedido confirmado ✅</h1>
        </div>
        <div style='padding:28px 32px;color:#1a1430;'>
          <p>Olá, <strong>{customer_name}</strong>. Recebemos seu pedido.</p>
          <div style='background:#f3f0ff;border:1px solid #e9d5ff;border-radius:14px;padding:14px;font-size:14px;color:#5b21b6;margin-bottom:18px;'>
            Referência: <strong>{external_ref}</strong><br>
            ID: <strong>{payment_id}</strong> &nbsp;|&nbsp;
            Método: <strong>{metodo_label}</strong> &nbsp;|&nbsp;
            Status: <strong>{status_pagamento}</strong>
          </div>
          <table width='100%' style='border-collapse:collapse;border:1px solid #eee;'>
            <thead><tr style='background:#faf7ff;'>
              <th style='padding:10px;text-align:left;color:#5b21b6;'>Item</th>
              <th style='padding:10px;text-align:center;color:#5b21b6;'>Qtd</th>
              <th style='padding:10px;text-align:right;color:#5b21b6;'>Subtotal</th>
            </tr></thead>
            <tbody>{linhas_html}</tbody>
          </table>
          <p style='font-size:18px;font-weight:800;text-align:right;margin:18px 0 22px;'>Total: {_brl(total)}</p>
          {cta}
        </div>
      </div>
    </div>
    """
    text_body = (
        f"HIPNUS COSMÉTICOS\nPedido confirmado\n\n"
        f"Referência: {external_ref} | ID: {payment_id}\n"
        f"Método: {metodo_label} | Status: {status_pagamento}\n"
        f"Total: {_brl(total)}\n"
        + (f"Link: {invoice_url}\n" if invoice_url else "")
    )
    return _send(to_email, "HIPNUS — Confirmação do seu pedido", html_body, text_body)
