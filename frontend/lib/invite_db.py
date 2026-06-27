"""
invite_db.py — HIPNUS COSMÉTICOS
===================================
Camada de acesso ao banco de dados para o domínio de Convites.

Versão standalone para uso direto no Streamlit, SEM dependência
do app/ (FastAPI). Toda a lógica de leitura/escrita de convites
está aqui, pronta para importar a partir de qualquer página.

Funciona em 2 modos:
  - Com banco SQLite local (Streamlit Cloud): persiste e valida tokens
  - Sem banco (fallback): retorna None (6_Convites cai no modo offline)

Uso:
    from lib.invite_db import validar_token_db, usar_token_db, criar_invite_db
"""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Garante PROJECT_ROOT e frontend/ no sys.path
_ROOT     = Path(__file__).resolve().parents[2]
_FRONTEND = Path(__file__).resolve().parents[1]
for _p in [str(_ROOT), str(_FRONTEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from lib.db_utils import get_db_session, resolve_db_url  # noqa: E402

INVITE_EXPIRY_DAYS = 7


# ─── Garantir tabela invites (idempotente) ──────────────────────────────────────
def _ensure_invite_table(engine) -> bool:
    """
    Cria a tabela 'invites' se ainda nao existir.
    Usa SQLAlchemy Core puro como fallback se os modelos ORM nao carregarem.
    Retorna True se a tabela estiver pronta.
    """
    # Tentativa 1: via modelos ORM
    try:
        from app.db.base import Base
        import app.domains.invites.models  # noqa: F401
        Base.metadata.create_all(bind=engine)
        return True
    except Exception:
        pass

    # Tentativa 2: via SQL puro (fallback robusto)
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("""
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
            """))
            conn.commit()
        return True
    except Exception:
        return False


# ─── Criar convite ────────────────────────────────────────────────────────────
def criar_invite_db(
    email: str,
    role: str,
    criado_por: str,
    app_url: str,
) -> dict | None:
    """
    Cria um novo convite no banco e retorna os dados.
    Garante que a tabela exista antes de inserir (create_all idempotente).
    Retorna None em caso de falha.
    """
    db, err = get_db_session()
    if not db:
        return None

    try:
        # Garante tabela antes de qualquer INSERT
        _ensure_invite_table(db.get_bind())

        token      = uuid.uuid4().hex
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=INVITE_EXPIRY_DAYS)
        signup_url = f"{app_url.rstrip('/')}/Cadastro_Parceiro?token={token}"

        # Tenta via ORM primeiro
        try:
            from app.domains.invites.models import Invite
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

        # Fallback: INSERT via SQL puro
        from sqlalchemy import text
        expires_str = expires_at.strftime("%Y-%m-%d %H:%M:%S")
        with db.get_bind().connect() as conn:
            conn.execute(text("""
                INSERT INTO invites (token, email, role, created_by, used, expires_at)
                VALUES (:token, :email, :role, :created_by, 0, :expires_at)
            """), {
                "token":      token,
                "email":      email,
                "role":       role,
                "created_by": criado_por,
                "expires_at": expires_str,
            })
            conn.commit()

        return {
            "token":      token,
            "email":      email,
            "role":       role,
            "created_by": criado_por,
            "signup_url": signup_url,
            "expires_at": expires_at.isoformat(),
            "email_sent": False,
            "origem":     "db_direto",
        }

    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        return None
    finally:
        db.close()


# ─── Validar token ───────────────────────────────────────────────────────────
def validar_token_db(token: str) -> dict | None:
    """
    Valida um token de convite diretamente no banco.
    Tenta via ORM; se falhar, usa SQL puro.
    Retorna dict com dados do convite ou None se invalido/expirado/usado.
    """
    db, err = get_db_session()
    if not db:
        return None

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Tentativa 1: ORM
    try:
        from app.domains.invites.models import Invite
        invite = db.query(Invite).filter(Invite.token == token).first()
        if not invite or invite.used:
            return None
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
        pass
    finally:
        db.close()

    # Tentativa 2: SQL puro
    db2, _ = get_db_session()
    if not db2:
        return None
    try:
        from sqlalchemy import text
        row = db2.execute(
            text("SELECT * FROM invites WHERE token = :token"),
            {"token": token},
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
            "id":         row_dict.get("id"),
            "token":      row_dict.get("token"),
            "email":      row_dict.get("email", ""),
            "role":       row_dict.get("role", "b2b"),
            "created_by": row_dict.get("created_by", ""),
            "used":       bool(row_dict.get("used", False)),
            "expires_at": exp.isoformat() if exp else "",
            "created_at": row_dict.get("created_at", ""),
        }
    except Exception:
        return None
    finally:
        db2.close()


# ─── Usar token (marcar como utilizado) ───────────────────────────────────────
def usar_token_db(token: str, dados: dict) -> tuple[bool, str]:
    """
    Marca o token como usado apos o cadastro ser concluido.
    Tenta via ORM; se falhar, usa SQL puro.
    Retorna (True, msg) em sucesso ou (False, erro) em falha.
    """
    now_str = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S")

    # Tentativa 1: ORM
    db, err = get_db_session()
    if db:
        try:
            from app.domains.invites.models import Invite
            invite = db.query(Invite).filter(Invite.token == token).first()
            if not invite:
                raise ValueError("Token nao encontrado via ORM.")
            if invite.used:
                return False, "Este convite ja foi utilizado."
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

    # Tentativa 2: SQL puro
    db2, err2 = get_db_session()
    if not db2:
        return False, f"Banco indisponível: {err2}"
    try:
        from sqlalchemy import text
        result = db2.execute(
            text("SELECT used FROM invites WHERE token = :token"),
            {"token": token},
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


# ─── Listar convites ───────────────────────────────────────────────────────────
def listar_invites_db() -> list[dict]:
    """Lista todos os convites do banco (para painel admin)."""
    db, err = get_db_session()
    if not db:
        return []

    # Tentativa 1: ORM
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
    finally:
        db.close()

    # Tentativa 2: SQL puro
    db2, _ = get_db_session()
    if not db2:
        return []
    try:
        from sqlalchemy import text
        rows = db2.execute(
            text("SELECT * FROM invites ORDER BY created_at DESC")
        ).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception:
        return []
    finally:
        db2.close()
