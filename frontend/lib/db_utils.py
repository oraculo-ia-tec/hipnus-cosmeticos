"""
db_utils.py — HIPNUS COSMÉTICOS
=================================
Utilitarios de banco de dados compartilhados pelo frontend Streamlit.

Problema resolvido:
  sqlite:///./data/hipnus.db usa ./ relativo ao cwd, que varia entre paginas
  do Streamlit Cloud. Isso fazia cada pagina abrir um arquivo .db diferente.

Solucao:
  Converter o path SQLite para absoluto usando PROJECT_ROOT como ancora fixa,
  garantindo que todas as paginas usem exatamente o mesmo arquivo .db.

Uso:
  from lib.db_utils import get_db_session, resolve_db_url
"""
from __future__ import annotations

import os
from pathlib import Path

# Ancora fixa: raiz do projeto (2 niveis acima de frontend/lib/)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_db_url() -> str:
    """
    Resolve DATABASE_URL com prioridade:
      1. st.secrets["DATABASE_URL"]          (Streamlit Cloud secrets.toml)
      2. st.secrets["default"]["DATABASE_URL"]
      3. os.environ["DATABASE_URL"]
      4. default: sqlite absoluto em PROJECT_ROOT/data/hipnus.db

    Paths SQLite relativos (sqlite:///./...) sao convertidos para absolutos
    usando PROJECT_ROOT como ancora, evitando que paginas diferentes
    resolvam caminhos diferentes dependendo do cwd.
    """
    raw = _read_raw_url()
    return _make_absolute(raw)


def _read_raw_url() -> str:
    """Le o valor bruto do DATABASE_URL dos secrets ou environ."""
    try:
        import streamlit as st
        val = st.secrets.get("DATABASE_URL")
        if val:
            return val.strip().strip('"').strip("'")
    except Exception:
        pass
    try:
        import streamlit as st
        val = st.secrets["default"].get("DATABASE_URL")
        if val:
            return val.strip().strip('"').strip("'")
    except Exception:
        pass
    val = os.environ.get("DATABASE_URL")
    if val:
        return val.strip()
    return f"sqlite:///{PROJECT_ROOT / 'data' / 'hipnus.db'}"


def _make_absolute(db_url: str) -> str:
    """
    Converte path SQLite relativo para absoluto.
    Ex: sqlite:///./data/hipnus.db  ->  sqlite:////home/user/app/data/hipnus.db
    MySQL/PostgreSQL URLs nao sao modificados.
    """
    if not db_url.startswith("sqlite:///"):
        return db_url

    path_str = db_url[len("sqlite:///"):]
    path = Path(path_str)

    if not path.is_absolute():
        # Remove ./ ou ../ e resolve relativo ao PROJECT_ROOT
        path = (PROJECT_ROOT / path).resolve()

    return f"sqlite:///{path}"


def get_db_session():
    """
    Abre sessao SQLAlchemy com DATABASE_URL absolutamente resolvido.
    Garante que o diretorio exista e que as tabelas da tabela invites existam.
    Retorna (session, error_str). Se falhar, session=None.
    """
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        import sys
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))

        db_url = resolve_db_url()

        # Garante diretorio
        if db_url.startswith("sqlite:///"):
            db_path = Path(db_url[len("sqlite:///"):])
            db_path.parent.mkdir(parents=True, exist_ok=True)

        connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
        engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)

        # Garante tabelas (idempotente)
        from app.db.base import Base
        import app.domains.invites.models  # noqa: F401
        try:
            import app.domains.users.models  # noqa: F401
        except ImportError:
            pass
        Base.metadata.create_all(bind=engine)

        Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        return Session(), None
    except Exception as exc:
        return None, str(exc)
