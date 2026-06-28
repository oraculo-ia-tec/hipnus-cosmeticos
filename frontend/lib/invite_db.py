"""
invite_db.py — HIPNUS COSMÉTICOS
===================================
Camada de acesso ao banco de dados para o domínio de Convites.

Funciona standalone (sem FastAPI).
"""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

_ROOT     = Path(__file__).resolve().parents[2]
_FRONTEND = Path(__file__).resolve().parents[1]
for _p in [str(_ROOT), str(_FRONTEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from lib.db_utils import get_db_session, resolve_db_url  # noqa: E402

INVITE_EXPIRY_DAYS = 7

_CREATE_INVITES = """
CREATE TABLE IF NOT EXISTS invites (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    token      VARCHAR(64)  NOT NULL UNIQUE,
    email      VARCHAR(180) NOT NULL,
    role       VARCHAR(30)  NOT NULL DEFAULT 'b2b',
    created_by VARCHAR(60)  NOT NULL DEFAULT 'system',
    used       BOOLEAN      NOT NULL DEFAULT 0,
    used_at    DATETIME,
    expires_at DATETIME     NOT NULL,
    created_at DATETIME     DEFAULT CURRENT_TIMESTAMP
)
"""


def _ensure_invite_table(engine) -> bool:
    try:
        from app.db.base import Base
        import app.domains.invites.models  # noqa: F401
        Base.metadata.create_all(bind=engine)
        return True
    except Exception:
        pass
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text(_CREATE_INVITES))
            conn.commit()
        return True
    except Exception:
        return False


def _ensure_table_db(db) -> None:
    """Garante tabela usando a sessão já aberta."""
    try:
        from sqlalchemy import text
        db.execute(text(_CREATE_INVITES))
        db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass


# ─── Criar convite (assinatura flexível) ────────────────────────────────────────
def criar_invite_db(
    email: str,
    role: str = "b2b",
    dias: int | None = None,
    criado_por: str = "admin",
    app_url: str = "",
) -> str:
    """
    Cria um convite no banco. Retorna o token gerado.
    A página 6_Convites chama: criar_invite_db(email=, role=, dias=)
    """
    db, err = get_db_session()
    if not db:
        raise RuntimeError(f"Banco indisponível: {err}")
    try:
        _ensure_table_db(db)
        from sqlalchemy import text
        token      = uuid.uuid4().hex
        expiry     = dias if dias is not None else INVITE_EXPIRY_DAYS
        expires_at = (datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=expiry))
        expires_str = expires_at.strftime("%Y-%m-%d %H:%M:%S")
        db.execute(text("""
            INSERT INTO invites (token, email, role, created_by, used, expires_at)
            VALUES (:token, :email, :role, :created_by, 0, :expires_at)
        """), {
            "token":      token,
            "email":      email.lower().strip(),
            "role":       role,
            "created_by": criado_por,
            "expires_at": expires_str,
        })
        db.commit()
        return token
    except Exception as exc:
        try:
            db.rollback()
        except Exception:
            pass
        raise exc
    finally:
        db.close()


# ─── Listar convites ─────────────────────────────────────────────────────────────────────
def listar_invites_db() -> list[dict]:
    """Lista todos os convites (para painel admin)."""
    db, err = get_db_session()
    if not db:
        return []
    try:
        _ensure_table_db(db)
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
            pass
        from sqlalchemy import text
        rows = db.execute(
            text("SELECT * FROM invites ORDER BY created_at DESC")
        ).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception:
        return []
    finally:
        db.close()


# ─── Deletar convite ─────────────────────────────────────────────────────────────────────
def deletar_invite_db(token: str) -> None:
    """Remove convite pelo token. Lança Exception em caso de erro."""
    db, err = get_db_session()
    if not db:
        raise RuntimeError(f"Banco indisponível: {err}")
    try:
        _ensure_table_db(db)
        from sqlalchemy import text
        db.execute(text("DELETE FROM invites WHERE token = :token"), {"token": token})
        db.commit()
    except Exception as exc:
        try:
            db.rollback()
        except Exception:
            pass
        raise exc
    finally:
        db.close()


# ─── Reativar convite ─────────────────────────────────────────────────────────────────────
def reativar_invite_db(token: str, dias: int = 30) -> None:
    """Reseta convite já utilizado, estendendo a validade. Lança Exception em erro."""
    db, err = get_db_session()
    if not db:
        raise RuntimeError(f"Banco indisponível: {err}")
    try:
        _ensure_table_db(db)
        from sqlalchemy import text
        nova_expiracao = (
            datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=dias)
        ).strftime("%Y-%m-%d %H:%M:%S")
        db.execute(text("""
            UPDATE invites
            SET used = 0, used_at = NULL, expires_at = :exp
            WHERE token = :token
        """), {"exp": nova_expiracao, "token": token})
        db.commit()
    except Exception as exc:
        try:
            db.rollback()
        except Exception:
            pass
        raise exc
    finally:
        db.close()


# ─── Validar token ──────────────────────────────────────────────────────────────────────
def validar_token_db(token: str) -> dict | None:
    db, err = get_db_session()
    if not db:
        return None
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    try:
        try:
            from app.domains.invites.models import Invite
            invite = db.query(Invite).filter(Invite.token == token).first()
            if not invite or invite.used or invite.expires_at < now:
                return None
            return {
                "id": invite.id, "token": invite.token,
                "email": invite.email, "role": invite.role,
                "created_by": invite.created_by, "used": invite.used,
                "expires_at": invite.expires_at.isoformat(),
                "created_at": invite.created_at.isoformat() if invite.created_at else "",
            }
        except Exception:
            pass
        from sqlalchemy import text
        row = db.execute(
            text("SELECT * FROM invites WHERE token = :token"), {"token": token}
        ).fetchone()
        if not row:
            return None
        row_dict = dict(row._mapping)
        if row_dict.get("used"):
            return None
        exp = row_dict.get("expires_at")
        if exp:
            if isinstance(exp, str):
                exp = datetime.fromisoformat(exp)
            if exp < now:
                return None
        return {
            "id": row_dict.get("id"), "token": row_dict.get("token"),
            "email": row_dict.get("email", ""), "role": row_dict.get("role", "b2b"),
            "created_by": row_dict.get("created_by", ""),
            "used": bool(row_dict.get("used", False)),
            "expires_at": exp.isoformat() if exp else "",
            "created_at": row_dict.get("created_at", ""),
        }
    except Exception:
        return None
    finally:
        db.close()


# ─── Usar token ───────────────────────────────────────────────────────────────────────────
def usar_token_db(token: str, dados: dict) -> tuple[bool, str]:
    now_str = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S")
    db, err = get_db_session()
    if db:
        try:
            from app.domains.invites.models import Invite
            invite = db.query(Invite).filter(Invite.token == token).first()
            if not invite:
                raise ValueError("Token não encontrado via ORM.")
            if invite.used:
                return False, "Este convite já foi utilizado."
            invite.used    = True
            invite.used_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.commit()
            return True, "Cadastro realizado com sucesso!"
        except ValueError as exc:
            return False, str(exc)
        except Exception:
            db.rollback()
        finally:
            db.close()
    db2, err2 = get_db_session()
    if not db2:
        return False, f"Banco indisponível: {err2}"
    try:
        from sqlalchemy import text
        result = db2.execute(
            text("SELECT used FROM invites WHERE token = :token"), {"token": token}
        ).fetchone()
        if not result:
            return False, "Token não encontrado."
        if result[0]:
            return False, "Este convite já foi utilizado."
        db2.execute(
            text("UPDATE invites SET used = 1, used_at = :now WHERE token = :token"),
            {"now": now_str, "token": token},
        )
        db2.commit()
        return True, "Cadastro realizado com sucesso!"
    except Exception as exc:
        db2.rollback()
        return False, str(exc)
    finally:
        db2.close()
