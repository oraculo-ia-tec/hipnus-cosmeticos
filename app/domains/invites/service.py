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
  - SMTP Hostinger via smtplib (config em app/core/config.py)
  - SQLAlchemy ORM com Session

Efeitos colaterais:
  - Cria registro na tabela `invites`
  - Envia e-mail ao destinatário (falha silenciosa com log)

Correções v2:
  - _build_signup_url: era ?invite= agora ?token= para alinhar com
    7_Cadastro_Parceiro.py que lê st.query_params.get('token').
"""
from __future__ import annotations

import logging
import smtplib
import ssl
import uuid
from datetime import datetime, timedelta, timezone
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate

from sqlalchemy.orm import Session

from app.core.config import settings
from app.domains.invites.models import Invite
from app.domains.invites.schemas import InviteCreate, InviteCreated, InviteOut

logger = logging.getLogger(__name__)

INVITE_EXPIRY_DAYS = 7


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _generate_token() -> str:
    """Gera um token UUID4 hexadecimal sem hífens (32 chars)."""
    return uuid.uuid4().hex


def _build_signup_url(token: str) -> str:
    """
    Monta a URL de cadastro personalizada para o convidado.

    FIX v2: parâmetro agora é ?token= (era ?invite=).
    7_Cadastro_Parceiro.py lê st.query_params.get('token'), portanto
    o nome do parâmetro deve ser exatamente 'token'.

    Usa APP_URL definido em settings (padrão: https://hipnus-cosmeticos.streamlit.app).
    """
    base = getattr(settings, "app_url", "https://hipnus-cosmeticos.streamlit.app")
    return f"{base}/Cadastro_Parceiro?token={token}"


def _send_invite_email(email: str, role: str, signup_url: str, created_by: str) -> bool:
    """
    Envia e-mail de convite via SMTP Hostinger.

    Parâmetros:
      email      — destinatário
      role       — perfil do convidado (b2b, b2c, admin)
      signup_url — URL de cadastro com token (?token=...)
      created_by — nome/username do admin que gerou o convite

    Retorna:
      True se enviado com sucesso, False em caso de erro (erro é logado).

    Boas práticas de entrega:
      - MIMEMultipart('alternative') com text/plain antes de text/html (RFC 2046)
      - Subject codificado via Header (RFC 2047) — sem emojis que causam rejeição
      - From montado via formataddr para suportar caracteres especiais
      - Headers Date e X-Mailer adicionados (reduzem score de spam)

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

    role_label = {
        "b2b":   "Profissional / Salão",
        "b2c":   "Cliente Final",
        "admin": "Administrador",
    }.get(role, role)
    expira = (datetime.now(timezone.utc) + timedelta(days=INVITE_EXPIRY_DAYS)).strftime("%d/%m/%Y")

    # ── Parte 1: texto plano (fallback obrigatório) ──────────────────────────
    text_body = (
        f"Voce foi convidado(a) por {created_by} para a plataforma HIPNUS COSMETICOS!\n\n"
        f"Perfil: {role_label}\n"
        f"Validade: {expira}\n\n"
        f"Acesse o link abaixo para criar sua conta:\n"
        f"{signup_url}\n\n"
        f"Se nao solicitou este convite, ignore este e-mail.\n"
        f"HIPNUS COSMETICOS - www.hipnuscosmeticos.com.br"
    )

    # ── Parte 2: HTML rico ───────────────────────────────────────────────────
    html_body = f"""\
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Convite HIPNUS</title>
</head>
<body style="margin:0;padding:0;background:#F6F4FB;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background:#F6F4FB;padding:40px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" border="0"
             style="background:#ffffff;border-radius:16px;border:1px solid #E7E3F2;">

        <!-- HEADER -->
        <tr>
          <td style="background:#7C3AED;padding:32px 40px;
                     text-align:center;border-radius:16px 16px 0 0;">
            <div style="width:52px;height:52px;border-radius:14px;
                        background:rgba(255,255,255,.18);display:inline-block;
                        line-height:52px;font-weight:900;font-size:1.4rem;
                        color:#fff;margin-bottom:12px;">H</div>
            <div style="font-size:1.3rem;font-weight:800;color:#fff;
                        letter-spacing:-.5px;font-family:Arial,sans-serif;">
              HIPNUS COSM&#201;TICOS
            </div>
            <div style="font-size:.72rem;color:rgba(255,255,255,.75);
                        letter-spacing:2px;text-transform:uppercase;
                        margin-top:4px;font-family:Arial,sans-serif;">
              Convite de Acesso
            </div>
          </td>
        </tr>

        <!-- BODY -->
        <tr>
          <td style="padding:36px 40px 28px;">
            <p style="font-size:1rem;color:#1A1430;margin:0 0 16px;
                      font-family:Arial,sans-serif;">Ol&#225;,</p>
            <p style="font-size:1rem;color:#1A1430;margin:0 0 20px;
                      line-height:1.6;font-family:Arial,sans-serif;">
              Voc&#234; foi convidado(a) por <strong>{created_by}</strong> para
              acessar a plataforma <strong>HIPNUS COSM&#201;TICOS</strong>
              como <strong>{role_label}</strong>.
            </p>
            <p style="font-size:.9rem;color:#6B6580;margin:0 0 28px;
                      font-family:Arial,sans-serif;">
              Clique no bot&#227;o abaixo para concluir seu cadastro.
              Este link expira em <strong>{expira}</strong>.
            </p>

            <!-- CTA BUTTON -->
            <table cellpadding="0" cellspacing="0" border="0" width="100%">
              <tr>
                <td align="center" style="padding:0 0 32px;">
                  <a href="{signup_url}"
                     style="display:inline-block;background:#7C3AED;
                            color:#ffffff;text-decoration:none;
                            font-size:15px;font-weight:bold;
                            padding:14px 40px;border-radius:10px;
                            font-family:Arial,sans-serif;">
                    Concluir meu cadastro
                  </a>
                </td>
              </tr>
            </table>

            <!-- LINK ALTERNATIVO -->
            <p style="font-size:.78rem;color:#9CA3AF;text-align:center;
                      margin:0 0 8px;font-family:Arial,sans-serif;">
              Ou copie o link abaixo:
            </p>
            <table cellpadding="0" cellspacing="0" border="0" width="100%">
              <tr>
                <td style="background:#F6F4FB;border:1px solid #E7E3F2;
                           border-radius:8px;padding:10px 16px;">
                  <span style="font-family:Courier New,monospace;font-size:12px;
                               color:#7C3AED;word-break:break-all;">
                    {signup_url}
                  </span>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- FOOTER -->
        <tr>
          <td style="padding:16px 40px 24px;border-top:1px solid #E7E3F2;
                     text-align:center;border-radius:0 0 16px 16px;">
            <p style="font-size:.72rem;color:#9CA3AF;margin:0;
                      line-height:1.6;font-family:Arial,sans-serif;">
              Este e-mail foi enviado pela plataforma HIPNUS COSM&#201;TICOS.<br>
              Se voc&#234; n&#227;o esperava este convite, ignore esta mensagem.
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"]      = Header("Seu convite para a plataforma HIPNUS COSMETICOS", "utf-8").encode()
    msg["From"]         = formataddr(("HIPNUS COSMETICOS", remetente))
    msg["To"]           = email
    msg["Date"]         = formatdate(localtime=False)
    msg["X-Mailer"]     = "HIPNUS-Service/2.0"
    msg["MIME-Version"] = "1.0"

    # ORDEM IMPORTA: text/plain primeiro, text/html por último (RFC 2046)
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html",  "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
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
      - URL gerada com ?token= (não ?invite=)
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
    """
    return db.query(Invite).order_by(Invite.created_at.desc()).all()


def get_invite_by_token(db: Session, token: str) -> Invite | None:
    """
    Busca um convite pelo token. Retorna None se não existir.
    """
    return db.query(Invite).filter(Invite.token == token).first()


def mark_invite_used(db: Session, token: str) -> Invite | None:
    """
    Marca um convite como utilizado.

    Parâmetros:
      db    — sessão SQLAlchemy
      token — token do convite

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
