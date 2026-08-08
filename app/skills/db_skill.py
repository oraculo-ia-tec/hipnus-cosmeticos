"""
db_skill.py — TÁLYA COSMÉTICOS
==================================
Skill de Banco de Dados: módulo compartilhado entre backend e frontend.

Centraliza a resolução do DATABASE_URL e a abertura de sessão SQLAlchemy,
eliminando a duplicação entre app/db/init_db.py e frontend/lib/db_utils.py.

Resolução de DATABASE_URL (em ordem de prioridade):
  1. st.secrets["DATABASE_URL"]      (Streamlit Cloud)
  2. st.secrets["default"]["DATABASE_URL"]
  3. os.environ["DATABASE_URL"]
  4. settings.database_url           (Pydantic Settings / .env)
  5. fallback: sqlite:///./data/talya.db

Garantias adicionais:
  - Paths SQLite relativos são convertidos para absolutos usando PROJECT_ROOT
    como âncora fixa — evita que páginas do Streamlit abram arquivos diferentes
    dependendo do cwd.
  - Diretório do arquivo SQLite é criado automaticamente se não existir.
  - Pool otimizado para Supabase PgBouncer (porta 6543) quando PostgreSQL.

Substitui:
  - app/db/init_db.py:_resolve_database_url() + init_db()
  - frontend/lib/db_utils.py:resolve_db_url() + get_db_session()

Uso no backend:
    from app.skills.db_skill import get_db_session, resolve_db_url, init_db

Uso no frontend (Streamlit):
    from app.skills.db_skill import get_db_session, resolve_db_url
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def _safe_url(url: str) -> str:
    """Redact password from a database URL before logging."""
    try:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(url)
        if parsed.password:
            netloc = parsed.netloc.replace(parsed.password, "****")
            return urlunparse(parsed._replace(netloc=netloc))
    except Exception:
        pass
    # For SQLite or unparseable URLs just show first 40 chars
    return url[:40] + ("..." if len(url) > 40 else "")

# Âncora fixa: raiz do projeto (3 níveis acima de app/skills/)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ─── Resolução de URL ─────────────────────────────────────────────────────────

def resolve_db_url() -> str:
    """
    Resolve o DATABASE_URL com prioridade:
      1. st.secrets["DATABASE_URL"]
      2. st.secrets["default"]["DATABASE_URL"]
      3. os.environ["DATABASE_URL"]
      4. settings.database_url

    Paths SQLite relativos (sqlite:///./...) são convertidos para absolutos
    usando PROJECT_ROOT como âncora.
    """
    raw = _read_raw_url()
    return _make_absolute(raw)


def _read_raw_url() -> str:
    """Lê o valor bruto de DATABASE_URL das fontes disponíveis."""
    # Streamlit secrets
    try:
        import streamlit as st
        val = st.secrets.get("DATABASE_URL")
        if val:
            return str(val).strip().strip('"').strip("'")
    except Exception:
        pass
    try:
        import streamlit as st
        val = st.secrets.get("default", {}).get("DATABASE_URL")
        if val:
            return str(val).strip().strip('"').strip("'")
    except Exception:
        pass

    # Variável de ambiente
    val = os.environ.get("DATABASE_URL")
    if val:
        return val.strip()

    # Pydantic settings
    try:
        from app.core.config import settings
        return settings.database_url
    except Exception:
        pass

    return f"sqlite:///{PROJECT_ROOT / 'data' / 'talya.db'}"


def _make_absolute(db_url: str) -> str:
    """
    Converte path SQLite relativo para absoluto usando PROJECT_ROOT.
    Ex: sqlite:///./data/talya.db → sqlite:////home/user/app/data/talya.db
    Outros dialetos (PostgreSQL, MySQL) não são modificados.
    """
    if not db_url.startswith("sqlite:///"):
        return db_url

    path_str = db_url[len("sqlite:///"):]
    path = Path(path_str)

    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()

    return f"sqlite:///{path}"


# ─── Pool helpers ─────────────────────────────────────────────────────────────

def _build_engine_kwargs(db_url: str) -> dict:
    """Retorna kwargs adequados ao banco detectado pela URL."""
    if db_url.startswith("sqlite"):
        return {
            "connect_args": {"check_same_thread": False},
            "pool_pre_ping": True,
        }
    # PostgreSQL — Supabase Pooler (PgBouncer transaction mode, porta 6543)
    return {
        "pool_size":    5,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,
        "pool_pre_ping": True,
    }


# ─── Sessão SQLAlchemy ────────────────────────────────────────────────────────

def get_db_session():
    """
    Abre uma sessão SQLAlchemy com DATABASE_URL absolutamente resolvido.

    Garante:
      - O diretório do arquivo SQLite existe (mkdir, idempotente)
      - As tabelas necessárias são criadas via Base.metadata.create_all

    Retorna:
      (session, None)       em sucesso
      (None, error_str)     em falha
    """
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        db_url = resolve_db_url()
        logger.debug("[db_skill] Abrindo sessão de banco (driver: %s)", "sqlite" if db_url.startswith("sqlite") else "postgres")

        if db_url.startswith("sqlite:///"):
            db_path = Path(db_url[len("sqlite:///"):])
            db_path.parent.mkdir(parents=True, exist_ok=True)

        engine = create_engine(db_url, **_build_engine_kwargs(db_url))
        _ensure_tables(engine)

        Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        return Session(), None

    except Exception as exc:
        logger.error("[db_skill] Falha ao abrir sessão: %s", exc)
        return None, str(exc)


def _ensure_tables(engine) -> None:
    """
    Importa todos os models e executa create_all (idempotente).
    Não falha se algum model não estiver acessível.
    """
    try:
        from app.db.base import Base

        # Models obrigatórios
        import app.domains.invites.models          # noqa: F401
        import app.domains.partners.models.parceiros  # noqa: F401

        # Models opcionais
        for mod in [
            "app.domains.users.models",
            "app.domains.catalog.models",
            "app.domains.orders.models",
            "app.domains.stores.models",
            "app.domains.payments.models",
        ]:
            try:
                __import__(mod)
            except ImportError:
                pass

        Base.metadata.create_all(bind=engine)
        logger.debug("[db_skill] Tabelas criadas/verificadas.")
    except Exception as exc:
        logger.warning("[db_skill] create_all ignorado: %s", exc)


# ─── init_db (compatibilidade com app/db/init_db.py) ─────────────────────────

def init_db() -> None:
    """
    Inicializa o banco de dados.
    Wrapper de compatibilidade para uso no startup do Streamlit e da API.
    """
    try:
        from sqlalchemy import create_engine

        db_url = resolve_db_url()
        logger.info("[db_skill] Inicializando banco (driver: %s)", "sqlite" if db_url.startswith("sqlite") else "postgres")

        engine = create_engine(db_url, **_build_engine_kwargs(db_url))
        _ensure_tables(engine)

        logger.info("[db_skill] Banco inicializado com sucesso.")
    except Exception as exc:
        logger.error("[db_skill] Falha ao inicializar banco: %s", exc)
