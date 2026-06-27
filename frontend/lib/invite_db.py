"""
invite_db.py — HIPNUS COSMÉTICOS
===================================
Camada de acesso ao banco de dados para o domínio de Convites.

Versão standalone para uso direto no Streamlit, SEM dependência
do app/ (FastAPI). Toda a lógica de leitura/escrita de convites
está aqui, pronta para importar a partir de qualquer página.

Uso:
    from lib.invite_db import validar_token_db, usar_token_db, criar_invite_db

Dependências:
    - lib.db_utils.get_db_session()   (path SQLite absoluto)
    - app.domains.invites.models.Invite  (modelo ORM existente)
    - app.db.base.Base               (metadata para create_all)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.db_utils import get_db_session  # noqa: E402

INVITE_EXPIRY_DAYS = 7


# ─── Garantir tabela ──────────────────────────────────────────────────────────────
def _ensure_tables(engine) -> None:
    """Cria a tabela invites se ainda não existir (idempotente)."""
    try:
        from app.db.base import Base
        import app.domains.invites.models  # noqa: F401
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass


# ─── Criar convite ──────────────────────────────────────────────────────────────
def criar_invite_db(
    email: str,
    role: str,
    criado_por: str,
    app_url: str,
) -> dict | None:
    """
    Cria um novo convite no banco e retorna os dados.

    Retorna dict com: token, email, role, created_by,
    signup_url, expires_at, email_sent, origem.
    Retorna None em caso de falha.
    """
    db, err = get_db_session()
    if not db:
        return None
    try:
        from app.domains.invites.models import Invite
        token      = uuid.uuid4().hex
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=INVITE_EXPIRY_DAYS)
        # URL correta para o Streamlit Cloud — sem número do arquivo, sem underscore duplo
        signup_url = f"{app_url.rstrip('/')}/Cadastro_Parceiro?token={token}"
        invite = Invite(
            token=token, email=email, role=role,
            created_by=criado_por, used=False, expires_at=expires_at,
        )
        db.add(invite)
        db.commit()
        db.refresh(invite)
        return {
            "token":      invite.token,
            "email":      invite.email,
            "role":       invite.role,
            "created_by": invite.created_by,
            "signup_url": signup_url,
            "expires_at": invite.expires_at.isoformat(),
            "email_sent": False,
            "origem":     "db_direto",
        }
    except Exception:
        db.rollback()
        return None
    finally:
        db.close()


# ─── Validar token ──────────────────────────────────────────────────────────────
def validar_token_db(token: str) -> dict | None:
    """
    Valida um token de convite diretamente no banco.

    Retorna os dados do convite se válido (não usado, não expirado).
    Retorna None se inválido, expirado ou já utilizado.
    """
    db, err = get_db_session()
    if not db:
        return None
    try:
        from app.domains.invites.models import Invite
        invite = db.query(Invite).filter(Invite.token == token).first()
        if not invite or invite.used:
            return None
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if invite.expires_at < now:
            return None
        return {
            "id":         invite.id,
            "token":      invite.token,
            "email":      invite.email,
            "role":       invite.role,
            "created_by": invite.created_by,
            "used":       invite.used,
            "expires_at": invite.expires_at.isoformat(),
            "created_at": invite.created_at.isoformat() if invite.created_at else "",
        }
    except Exception:
        return None
    finally:
        db.close()


# ─── Usar token (marcar como utilizado) ──────────────────────────────────────────
def usar_token_db(token: str, dados: dict) -> tuple[bool, str]:
    """
    Marca o token como usado após o cadastro ser concluído.

    Retorna (True, mensagem) em caso de sucesso.
    Retorna (False, erro) em caso de falha.
    """
    db, err = get_db_session()
    if not db:
        return False, f"Banco indisponível: {err}"
    try:
        from app.domains.invites.models import Invite
        invite = db.query(Invite).filter(Invite.token == token).first()
        if not invite:
            return False, "Token não encontrado."
        if invite.used:
            return False, "Este convite já foi utilizado."
        invite.used    = True
        invite.used_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        return True, "Cadastro realizado com sucesso!"
    except Exception as exc:
        db.rollback()
        return False, str(exc)
    finally:
        db.close()


# ─── Listar convites ──────────────────────────────────────────────────────────────
def listar_invites_db() -> list[dict]:
    """Lista todos os convites do banco (para painel admin)."""
    db, err = get_db_session()
    if not db:
        return []
    try:
        from app.domains.invites.models import Invite
        invites = db.query(Invite).order_by(Invite.created_at.desc()).all()
        return [
            {
                "id":         i.id,
                "token":      i.token,
                "email":      i.email,
                "role":       i.role,
                "created_by": i.created_by,
                "used":       i.used,
                "used_at":    i.used_at.isoformat() if i.used_at else None,
                "expires_at": i.expires_at.isoformat(),
                "created_at": i.created_at.isoformat() if i.created_at else "",
            }
            for i in invites
        ]
    except Exception:
        return []
    finally:
        db.close()
