"""
email_skill.py — TÁLYA COSMÉTICOS
=====================================
Skill de E-mail: módulo compartilhado entre backend e frontend.

Centraliza TODA a lógica de envio de e-mail via SMTP (Hostinger ou qualquer
servidor STARTTLS/SMTP_SSL). Inclui templates prontos para:
  - Convite de parceiro (send_invite_email)
  - Confirmação de pedido (send_order_confirmation_email)
  - E-mail de teste (send_test_email)
  - Envio genérico (send_email)

Resolução de credenciais SMTP (em ordem de prioridade):
  1. st.secrets["email"][key]   — seção [email] no secrets.toml
  2. st.secrets[key]            — raiz do secrets.toml
  3. os.environ[key]
  4. settings.smtp_*            — Pydantic Settings / .env

Substitui:
  - app/domains/invites/service.py:_send_invite_email()
  - frontend/lib/email_service.py

Uso:
    from app.skills.email_skill import send_invite_email, send_email, smtp_status
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

INVITE_EXPIRY_DAYS = 7


# ─── Resolução de credenciais ────────────────────────────────────────────────

def _secret(key: str, default: str = "") -> str:
    """
    Lê credencial com fallback em 4 camadas:
      1. st.secrets["email"][key]
      2. st.secrets[key]
      3. os.environ[key]
      4. settings.smtp_*
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

    val = os.environ.get(key, "")
    if val:
        return val.strip()

    # Pydantic settings fallback
    try:
        from app.core.config import settings
        mapping = {
            "EMAIL_HOST":     settings.smtp_host,
            "SMTP_HOST":      settings.smtp_host,
            "EMAIL_PORT":     str(settings.smtp_port),
            "SMTP_PORT":      str(settings.smtp_port),
            "EMAIL_USERNAME": settings.smtp_user,
            "SMTP_USER":      settings.smtp_user,
            "EMAIL_PASSWORD": settings.smtp_password,
            "SMTP_PASSWORD":  settings.smtp_password,
            "EMAIL_REMETENTE": settings.smtp_from,
            "SMTP_FROM":      settings.smtp_from,
        }
        val = mapping.get(key, "")
        if val:
            return str(val).strip()
    except Exception:
        pass

    return default


def _get_smtp_config() -> dict:
    use_ssl = _secret("EMAIL_USE_SSL", "false").lower() == "true"
    use_tls = _secret("EMAIL_USE_TLS", "true").lower() == "true"
    host    = _secret("EMAIL_HOST",     "") or _secret("SMTP_HOST",     "smtp.hostinger.com")
    port    = int(_secret("EMAIL_PORT", "") or _secret("SMTP_PORT",     "587"))
    user    = _secret("EMAIL_USERNAME", "") or _secret("SMTP_USER",     "")
    pwd     = _secret("EMAIL_PASSWORD", "") or _secret("SMTP_PASSWORD", "")
    sender  = (
        _secret("EMAIL_REMETENTE", "")
        or _secret("SMTP_FROM", "")
        or user
        or "noreply@talyacosmeticos.com.br"
    )
    return {
        "host":    host,
        "port":    port,
        "user":    user,
        "password": pwd,
        "from":    sender,
        "use_tls": use_tls,
        "use_ssl": use_ssl,
    }


# ─── Diagnóstico ──────────────────────────────────────────────────────────────

def smtp_status() -> dict:
    """Retorna estado da configuração SMTP sem expor credenciais."""
    cfg = _get_smtp_config()
    return {
        "host":                cfg["host"],
        "port":                cfg["port"],
        "user_configured":     bool(cfg["user"]),
        "password_configured": bool(cfg["password"]),
        "from_email":          cfg["from"],
        "use_tls":             cfg["use_tls"],
        "use_ssl":             cfg["use_ssl"],
        "ready": bool(cfg["host"] and cfg["port"] and cfg["user"] and cfg["password"]),
    }


# ─── Engine de envio ──────────────────────────────────────────────────────────

def _send(to_email: str, subject: str, html_body: str, text_body: str) -> tuple[bool, str]:
    """Envia e-mail via SMTP_SSL (porta 465) ou STARTTLS (porta 587)."""
    cfg = _get_smtp_config()
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = Header(subject, "utf-8").encode()
        msg["From"]    = formataddr(("TÁLYA COSMÉTICOS", cfg["from"]))
        msg["To"]      = to_email
        msg["Date"]    = formatdate(localtime=False)
        msg["X-Mailer"] = "TALYA-Service/2.0"
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html",  "utf-8"))

        context = ssl.create_default_context()

        if cfg["use_ssl"]:
            with smtplib.SMTP_SSL(cfg["host"], cfg["port"], context=context, timeout=20) as s:
                s.login(cfg["user"], cfg["password"])
                s.sendmail(cfg["from"], to_email, msg.as_string())
        else:
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


# ─── API pública ──────────────────────────────────────────────────────────────

def send_email(
    to_email: str | Iterable[str],
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> tuple[bool, str]:
    """
    Envio genérico. Aceita um ou múltiplos destinatários.

    Retorna (True, mensagem) em sucesso, (False, mensagem de erro) em falha.
    """
    if not smtp_status()["ready"]:
        return False, (
            "SMTP incompleto. Configure EMAIL_HOST, EMAIL_PORT, "
            "EMAIL_USERNAME, EMAIL_PASSWORD nos Secrets ou .env."
        )
    recipients = [to_email] if isinstance(to_email, str) else list(to_email)
    errors = []
    for recipient in recipients:
        ok, msg = _send(
            recipient,
            subject,
            html_body,
            text_body or "Seu cliente de e-mail não suporta HTML.",
        )
        if not ok:
            errors.append(f"{recipient}: {msg}")
    if errors:
        return False, " | ".join(errors)
    return True, "E-mail(s) enviado(s) com sucesso."


def send_test_email(to_email: str) -> tuple[bool, str]:
    """Envia e-mail de teste com layout padrão Tálya."""
    html = """\
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant:ital,wght@0,600;1,500&family=Manrope:wght@400;600;700&display=swap');
</style>
</head>
<body style="margin:0;padding:0;background:#fbf6f2;font-family:'Manrope','Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#fbf6f2;padding:40px 0;">
  <tr><td align="center">
    <table width="560" cellpadding="0" cellspacing="0"
           style="background:#fff;border-radius:16px;border:1px solid #e8d5c0;overflow:hidden;">
      <tr><td style="background:linear-gradient(135deg,#b76e79 0%,#c9a04e 100%);
                     padding:32px 40px;text-align:center;">
        <div style="font-family:'Cormorant',Georgia,serif;font-size:26px;font-weight:600;
                    font-style:italic;color:#fff;letter-spacing:1px;">Tálya Cosméticos</div>
        <div style="font-size:11px;color:rgba(255,255,255,.85);letter-spacing:2.5px;
                    text-transform:uppercase;margin-top:6px;font-weight:600;">
          Diagnóstico de E-mail
        </div>
      </td></tr>
      <tr><td style="padding:32px 40px;color:#3a2620;">
        <p style="font-size:15px;line-height:1.7;margin:0 0 16px;">
          Se você recebeu esta mensagem, o <strong>SMTP está ativo</strong>
          e configurado corretamente.
        </p>
        <div style="background:#fdf5ef;border:1px solid #f1ddd0;border-radius:10px;
                    padding:14px 18px;font-size:13px;color:#6b4f43;margin-top:8px;">
          ✅ Servidor SMTP respondendo — Tálya Cosméticos
        </div>
      </td></tr>
      <tr><td style="padding:16px 40px 24px;border-top:1px solid #f1ddd0;text-align:center;">
        <p style="font-size:11px;color:#a08876;margin:0;line-height:1.6;">
          TÁLYA COSMÉTICOS &copy; 2026 — Este é um e-mail automático de diagnóstico.
        </p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>"""
    text = "Teste de SMTP da plataforma TÁLYA COSMÉTICOS. Configuração OK."
    return send_email(to_email, "TÁLYA — Teste de SMTP", html, text)


def send_invite_email(
    email: str,
    role: str,
    signup_url: str,
    created_by: str = "system",
) -> tuple[bool, str]:
    """
    Envia convite de parceiro com template visual.

    Args:
        email:      e-mail do destinatário
        role:       perfil do convidado ('b2b', 'b2c', 'admin')
        signup_url: URL de cadastro com token (?token=...)
        created_by: nome/username de quem gerou o convite

    Retorna (True, msg) em sucesso, (False, msg_erro) em falha.
    """
    if not smtp_status()["ready"]:
        return False, (
            "SMTP incompleto. Configure EMAIL_HOST, EMAIL_PORT, "
            "EMAIL_USERNAME, EMAIL_PASSWORD nos Secrets ou .env."
        )

    role_label = {
        "b2b":   "Profissional / Salão",
        "b2c":   "Cliente Final",
        "admin": "Administrador",
    }.get(role, role)
    expira = (datetime.utcnow() + timedelta(days=INVITE_EXPIRY_DAYS)).strftime("%d/%m/%Y")

    html_body = f"""\
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant:ital,wght@0,600;1,500&family=Manrope:wght@400;600;700&display=swap');
</style>
</head>
<body style="margin:0;padding:0;background:#fbf6f2;font-family:'Manrope','Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0"
       style="background:#fbf6f2;padding:40px 0;">
  <tr><td align="center">
    <table width="560" cellpadding="0" cellspacing="0"
           style="background:#fff;border-radius:16px;border:1px solid #e8d5c0;overflow:hidden;">

      <!-- HEADER -->
      <tr><td style="background:linear-gradient(135deg,#b76e79 0%,#c9a04e 100%);
                     padding:32px 40px;text-align:center;">
        <div style="font-family:'Cormorant',Georgia,serif;font-size:26px;font-weight:600;
                    font-style:italic;color:#fff;letter-spacing:1px;">
          Tálya Cosméticos
        </div>
        <div style="font-size:11px;color:rgba(255,255,255,.85);letter-spacing:2.5px;
                    text-transform:uppercase;margin-top:6px;font-weight:600;">
          Convite de Acesso
        </div>
      </td></tr>

      <!-- BODY -->
      <tr><td style="padding:36px 40px 28px;">
        <p style="font-size:15px;color:#3a2620;margin:0 0 20px;line-height:1.7;">
          Voc&#234; foi convidado(a) por <strong>{created_by}</strong> para a plataforma
          <strong>Tálya Cosméticos</strong> como <strong>{role_label}</strong>.
        </p>
        <p style="font-size:13px;color:#6b4f43;margin:0 0 28px;line-height:1.6;">
          Este link expira em <strong>{expira}</strong>.
        </p>
        <!-- CTA -->
        <table cellpadding="0" cellspacing="0" width="100%">
          <tr><td align="center" style="padding:0 0 24px;">
            <a href="{signup_url}"
               style="display:inline-block;background:#b76e79;color:#fff;
                      text-decoration:none;font-size:15px;font-weight:700;
                      padding:14px 40px;border-radius:10px;letter-spacing:.3px;">
              Concluir meu cadastro
            </a>
          </td></tr>
        </table>
        <!-- Link alternativo -->
        <div style="background:#fdf5ef;border:1px solid #f1ddd0;border-radius:8px;
                    padding:10px 16px;">
          <span style="font-family:'Courier New',monospace;font-size:12px;
                       color:#7c5c4a;word-break:break-all;">{signup_url}</span>
        </div>
      </td></tr>

      <!-- FOOTER -->
      <tr><td style="padding:16px 40px 24px;border-top:1px solid #f1ddd0;text-align:center;">
        <p style="font-size:11px;color:#a08876;margin:0;line-height:1.6;">
          TÁLYA COSMÉTICOS &copy; 2026 — Se voc&#234; n&#227;o esperava este convite,
          ignore esta mensagem.
        </p>
      </td></tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""

    text_body = (
        f"Você foi convidado(a) por {created_by} para a TÁLYA COSMÉTICOS!\n\n"
        f"Perfil: {role_label}\nVálido até: {expira}\n\n"
        f"Acesse o link:\n{signup_url}\n\n"
        "Se não esperava este convite, ignore esta mensagem."
    )

    return _send(
        email,
        "Seu convite para a plataforma TÁLYA COSMÉTICOS",
        html_body,
        text_body,
    )


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
    """
    Envia e-mail de confirmação de pedido ao cliente.

    Args:
        to_email:       e-mail do cliente
        customer_name:  nome do cliente
        billing_type:   'PIX' | 'BOLETO' | 'CREDIT_CARD'
        resultado:      dict retornado pelo checkout_service (totais, payment_id, etc.)
        itens:          lista de dicts com {name, qty, price}
    """
    if not smtp_status()["ready"]:
        return False, "SMTP não configurado."

    total            = resultado.get("totais", {}).get("total", 0)
    external_ref     = resultado.get("external_ref", "")
    payment_id       = resultado.get("payment_id", "")
    invoice_url      = resultado.get("invoice_url", "")
    status_pagamento = resultado.get("status", "")
    metodo_label     = {"PIX": "PIX", "BOLETO": "Boleto", "CREDIT_CARD": "Cartão"}.get(
        billing_type, billing_type
    )

    linhas_html = "".join(
        f"<tr>"
        f"<td style='padding:10px 14px;border-bottom:1px solid #f1ddd0;color:#3a2620;'>{item['name']}</td>"
        f"<td style='padding:10px 14px;border-bottom:1px solid #f1ddd0;text-align:center;color:#6b4f43;'>"
        f"{item['qty']}</td>"
        f"<td style='padding:10px 14px;border-bottom:1px solid #f1ddd0;text-align:right;color:#3a2620;'>"
        f"{_brl(Decimal(str(item['price'])) * Decimal(str(item['qty'])))}</td>"
        f"</tr>"
        for item in itens
    )
    cta = (
        f"<a href='{invoice_url}' style='display:inline-block;background:#b76e79;color:#fff;"
        f"text-decoration:none;font-size:15px;font-weight:700;padding:14px 28px;"
        f"border-radius:10px;letter-spacing:.3px;'>Abrir pagamento</a>"
        if invoice_url else ""
    )

    html_body = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant:ital,wght@0,600;1,500&family=Manrope:wght@400;600;700&display=swap');
</style>
</head>
<body style="margin:0;padding:0;background:#fbf6f2;font-family:'Manrope','Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#fbf6f2;padding:40px 0;">
  <tr><td align="center">
    <table width="620" cellpadding="0" cellspacing="0"
           style="background:#fff;border-radius:16px;border:1px solid #e8d5c0;overflow:hidden;">

      <!-- HEADER -->
      <tr><td style="background:linear-gradient(135deg,#b76e79 0%,#c9a04e 100%);
                     padding:28px 36px;text-align:center;">
        <div style="font-family:'Cormorant',Georgia,serif;font-size:26px;font-weight:600;
                    font-style:italic;color:#fff;letter-spacing:1px;">
          Tálya Cosméticos
        </div>
        <div style="font-size:11px;color:rgba(255,255,255,.85);letter-spacing:2.5px;
                    text-transform:uppercase;margin-top:6px;font-weight:600;">
          Confirmação de Pedido ✓
        </div>
      </td></tr>

      <!-- BODY -->
      <tr><td style="padding:28px 36px;color:#3a2620;">
        <p style="font-size:15px;margin:0 0 18px;line-height:1.7;">
          Olá, <strong>{customer_name}</strong>. Recebemos seu pedido com sucesso!
        </p>
        <div style="background:#fdf5ef;border:1px solid #f1ddd0;border-radius:12px;
                    padding:14px 18px;font-size:13px;color:#6b4f43;margin-bottom:20px;
                    line-height:1.8;">
          <strong>Referência:</strong> {external_ref}<br>
          <strong>ID do Pagamento:</strong> {payment_id}<br>
          <strong>Método:</strong> {metodo_label} &nbsp;|&nbsp;
          <strong>Status:</strong> {status_pagamento}
        </div>

        <!-- Tabela de itens -->
        <table width="100%" style="border-collapse:collapse;border:1px solid #e8d5c0;
                                    border-radius:10px;overflow:hidden;font-size:14px;">
          <thead>
            <tr style="background:#fbf6f2;">
              <th style="padding:10px 14px;text-align:left;color:#3a2620;
                         border-bottom:1px solid #e8d5c0;font-weight:700;">Item</th>
              <th style="padding:10px 14px;text-align:center;color:#3a2620;
                         border-bottom:1px solid #e8d5c0;font-weight:700;">Qtd</th>
              <th style="padding:10px 14px;text-align:right;color:#3a2620;
                         border-bottom:1px solid #e8d5c0;font-weight:700;">Subtotal</th>
            </tr>
          </thead>
          <tbody>{linhas_html}</tbody>
        </table>

        <p style="font-size:17px;font-weight:800;text-align:right;
                  margin:18px 0 22px;color:#3a2620;">
          Total: {_brl(total)}
        </p>
        {cta}
      </td></tr>

      <!-- FOOTER -->
      <tr><td style="padding:16px 36px 24px;border-top:1px solid #f1ddd0;text-align:center;">
        <p style="font-size:11px;color:#a08876;margin:0;line-height:1.6;">
          TÁLYA COSMÉTICOS &copy; 2026 — Este é um e-mail automático, não responda.
        </p>
      </td></tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""

    text_body = (
        f"TÁLYA COSMÉTICOS — Pedido confirmado\n\n"
        f"Referência: {external_ref} | ID: {payment_id}\n"
        f"Método: {metodo_label} | Status: {status_pagamento}\n"
        f"Total: {_brl(total)}\n"
        + (f"Link: {invoice_url}\n" if invoice_url else "")
    )

    return send_email(to_email, "TÁLYA — Confirmação do seu pedido", html_body, text_body)
