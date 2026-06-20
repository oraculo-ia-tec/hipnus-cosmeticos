"""
service.py — Domínio Invites
==============================
Lógica de negócio para criação, listagem e uso de convites.

Responsabilidades:
  - Gerar token UUID único para cada convite
  - Persistir o convite no banco (SQLite local / MySQL Hostinger)
  - Enviar e-mail de convite via SMTP Hostinger
  - Listar convites existentes (todos ou por e-mail)
  - Marcar convite como usado no momento do cadastro
  - Validar expiração e uso duplo

Integrações:
  - SMTP Hostinger via smtplib (config em frontend/lib/config.py e app/core/config.py)
  - SQLAlchemy ORM com Session

Efeitos colaterais:
  - Cria registro na tabela `invites`
  - Envia e-mail ao destinatário (falha silenciosa com log)
"""
from __future__ import annotations

import logging
import smtplib
import uuid
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy.orm import Session

from app.core.config import settings
from app.domains.invites.models import Invite
from app.domains.invites.schemas import InviteCreate, InviteCreated

logger = logging.getLogger(__name__)

INVITE_EXPIRY_DAYS = 7


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _generate_token() -> str:
    """Gera um token UUID4 hexadecimal sem hífens (32 chars)."""
    return uuid.uuid4().hex


def _build_signup_url(token: str) -> str:
    """
    Monta a URL de cadastro personalizada para o convidado.

    Usa APP_URL definido em settings (padrão: https://hipnus-cosmeticos.streamlit.app).
    URL formato: {APP_URL}/Cadastro_Parceiro?invite={token}
    """
    base = getattr(settings, "app_url", "https://hipnus-cosmeticos.streamlit.app")
    return f"{base}/Cadastro_Parceiro?invite={token}"


def _send_invite_email(email: str, role: str, signup_url: str, created_by: str) -> bool:
    """
    Envia e-mail de convite via SMTP Hostinger.

    Parâmetros:
      email      — destinatário
      role       — perfil do convidado (b2b, b2c, admin)
      signup_url — URL de cadastro com token
      created_by — nome/username do admin que gerou o convite

    Retorna:
      True se enviado com sucesso, False em caso de erro (erro é logado).

    Efeitos colaterais:
      Abre conexão SMTP com o servidor Hostinger e envia o e-mail.
    """
    smtp_host = getattr(settings, "smtp_host", "smtp.hostinger.com")
    smtp_port = int(getattr(settings, "smtp_port", 587))
    smtp_user = getattr(settings, "smtp_user", "")
    smtp_pass = getattr(settings, "smtp_pass", "")
    remetente = getattr(settings, "smtp_sender", smtp_user)

    if not smtp_user or not smtp_pass:
        logger.warning("SMTP não configurado — e-mail de convite não enviado.")
        return False

    role_label = {"b2b": "Profissional / Salão", "b2c": "Cliente Final", "admin": "Administrador"}.get(role, role)

    html_body = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head><meta charset="UTF-8"></head>
    <body style="margin:0;padding:0;background:#f6f4fb;font-family:'Segoe UI',Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f6f4fb;padding:40px 0;">
        <tr><td align="center">
          <table width="560" cellpadding="0" cellspacing="0"
                 style="background:#ffffff;border-radius:16px;overflow:hidden;
                        box-shadow:0 8px 32px rgba(124,58,237,.12);">
            <!-- Header -->
            <tr>
              <td style="background:linear-gradient(135deg,#7C3AED 0%,#5B21B6 100%);
                         padding:32px 40px 28px;text-align:center;">
                <div style="width:52px;height:52px;border-radius:14px;background:rgba(255,255,255,.18);
                            display:inline-flex;align-items:center;justify-content:center;
                            font-weight:900;font-size:1.5rem;color:#fff;margin-bottom:12px;">H</div>
                <div style="font-size:1.4rem;font-weight:800;color:#fff;letter-spacing:-.5px;">
                  HIPNUS COSMÉTICOS
                </div>
                <div style="font-size:.75rem;color:rgba(255,255,255,.75);letter-spacing:2px;
                            text-transform:uppercase;margin-top:4px;">Convite de Acesso</div>
              </td>
            </tr>
            <!-- Body -->
            <tr>
              <td style="padding:36px 40px 28px;">
                <p style="font-size:1rem;color:#1A1430;margin:0 0 16px;">Olá,</p>
                <p style="font-size:1rem;color:#1A1430;margin:0 0 24px;line-height:1.6;">
                  Você foi convidado(a) por <strong>{created_by}</strong> para acessar a plataforma
                  <strong>HIPNUS COSMÉTICOS</strong> como <strong>{role_label}</strong>.
                </p>
                <p style="font-size:.9rem;color:#6B6580;margin:0 0 24px;">
                  Clique no botão abaixo para concluir seu cadastro. Este link expira em
                  <strong>{INVITE_EXPIRY_DAYS} dias</strong>.
                </p>
                <!-- CTA -->
                <div style="text-align:center;margin:28px 0;">
                  <a href="{signup_url}"
                     style="display:inline-block;background:linear-gradient(135deg,#7C3AED,#5B21B6);
                            color:#fff;font-weight:700;font-size:1rem;padding:14px 36px;
                            border-radius:10px;text-decoration:none;letter-spacing:.2px;
                            box-shadow:0 4px 16px rgba(124,58,237,.35);">
                    Concluir meu cadastro →
                  </a>
                </div>
                <!-- Link alternativo -->
                <p style="font-size:.78rem;color:#9CA3AF;text-align:center;margin:0 0 8px;">
                  Ou copie o link abaixo:
                </p>
                <p style="font-size:.75rem;color:#7C3AED;text-align:center;
                          word-break:break-all;background:#F3F0FF;padding:10px 16px;
                          border-radius:8px;margin:0;">
                  {signup_url}
                </p>
              </td>
            </tr>
            <!-- Footer -->
            <tr>
              <td style="padding:16px 40px 28px;border-top:1px solid #E7E3F2;">
                <p style="font-size:.72rem;color:#9CA3AF;text-align:center;margin:0;line-height:1.6;">
                  Este e-mail foi enviado pela plataforma HIPNUS COSMÉTICOS.<br>
                  Se você não esperava este convite, ignore esta mensagem.
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
    msg["Subject"] = "🎉 Você foi convidado(a) para a HIPNUS COSMÉTICOS"
    msg["From"]    = remetente
    msg["To"]      = email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(remetente, [email], msg.as_string())
        logger.info("E-mail de convite enviado para %s", email)
        return True
    except Exception as exc:
        logger.error("Falha ao enviar e-mail de convite para %s: %s", email, exc)
        return False


# ─── CRUD ────────────────────────────────────────────────────────────────────

def create_invite(
    db: Session,
    payload: InviteCreate,
    created_by: str = "system",
) -> InviteCreated:
    """
    Cria um novo convite no banco e envia o e-mail ao destinatário.

    Parâmetros:
      db         — sessão SQLAlchemy
      payload    — InviteCreate com email e role
      created_by — username do admin que gerou o convite

    Retorno:
      InviteCreated com token, signup_url e status do envio de e-mail.

    Regras de negócio:
      - Token gerado como UUID4 hex (32 chars, único)
      - Expiração: criado_em + 7 dias
      - E-mail enviado via SMTP Hostinger (falha silenciosa)
      - Múltiplos convites para o mesmo e-mail são permitidos
    """
    token      = _generate_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=INVITE_EXPIRY_DAYS)
    signup_url = _build_signup_url(token)

    invite = Invite(
        token=token,
        email=payload.email,
        role=payload.role,
        created_by=created_by,
        used=False,
        expires_at=expires_at,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    email_sent = _send_invite_email(
        email=invite.email,
        role=invite.role,
        signup_url=signup_url,
        created_by=created_by,
    )

    return InviteCreated(
        **InviteOut.model_validate(invite).model_dump(),
        signup_url=signup_url,
        email_sent=email_sent,
    )


def list_invites(db: Session) -> list[Invite]:
    """
    Retorna todos os convites ordenados do mais recente para o mais antigo.

    Parâmetros:
      db — sessão SQLAlchemy

    Retorno:
      Lista de objetos Invite.
    """
    return db.query(Invite).order_by(Invite.created_at.desc()).all()


def get_invite_by_token(db: Session, token: str) -> Invite | None:
    """
    Busca um convite pelo token.

    Retorna None se o token não existir.
    """
    return db.query(Invite).filter(Invite.token == token).first()


def mark_invite_used(db: Session, token: str) -> Invite | None:
    """
    Marca um convite como utilizado.

    Parâmetros:
      db    — sessão SQLAlchemy
      token — token do convite

    Retorno:
      Invite atualizado ou None se o token não existir.

    Regras de negócio:
      - Se já usado, retorna o invite sem alteração
      - Registra o timestamp de uso em used_at
    """
    invite = get_invite_by_token(db, token)
    if not invite or invite.used:
        return invite
    invite.used    = True
    invite.used_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(invite)
    return invite
