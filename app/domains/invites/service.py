"""
service.py — Domínio Invites
==============================
Lógica de negócio para criação, listagem e uso de convites.

O envio de e-mail foi centralizado em app/skills/email_skill.py.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.domains.invites.models import Invite
from app.domains.invites.schemas import InviteCreate, InviteCreated, InviteOut
from app.skills.email_skill import send_invite_email as _skill_send_invite_email

logger = logging.getLogger(__name__)

INVITE_EXPIRY_DAYS = 7


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _generate_token() -> str:
    """Gera um token UUID4 hexadecimal sem hífens (32 chars)."""
    return uuid.uuid4().hex


def _build_signup_url(token: str) -> str:
    """
    Monta a URL de cadastro personalizada para o convidado.
    Parâmetro: ?token= (alinhado com 7_Cadastro_Parceiro.py).
    """
    base = getattr(settings, "app_url", "https://talya-cosmeticos.streamlit.app")
    return f"{base}/Cadastro_Parceiro?token={token}"


def _send_invite_email(email: str, role: str, signup_url: str, created_by: str) -> bool:
    """Delega para app.skills.email_skill.send_invite_email."""
    try:
        ok, _ = _skill_send_invite_email(
            email=email,
            role=role,
            signup_url=signup_url,
            created_by=created_by,
        )
        return ok
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
