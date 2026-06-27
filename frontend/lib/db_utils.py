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
import sys
from pathlib import Path

# Ancora fixa: raiz do projeto (2 niveis acima de frontend/lib/)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = Path(__file__).resolve().parents[1]

# Garante paths no sys.path imediatamente ao importar este modulo
for _p in [str(PROJECT_ROOT), str(FRONTEND_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


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
    # Default: SQLite absoluto dentro do projeto
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
        path = (PROJECT_ROOT / path).resolve()

    return f"sqlite:///{path}"


def get_db_session():
    """
    Abre sessao SQLAlchemy com DATABASE_URL absolutamente resolvido.

    Garante:
      - PROJECT_ROOT e frontend/ estao no sys.path antes de qualquer import
      - O diretorio do SQLite existe (mkdir)
      - As tabelas necessarias sao criadas (create_all, idempotente)

    Retorna (session, None) em sucesso ou (None, error_str) em falha.
    """
    # Dupla garantia de paths (caso seja chamado antes do modulo ser inicializado)
    for _p in [str(PROJECT_ROOT), str(FRONTEND_DIR)]:
        if _p not in sys.path:
            sys.path.insert(0, _p)

    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        db_url = resolve_db_url()

        # Garante diretorio do SQLite
        if db_url.startswith("sqlite:///"):
            db_path = Path(db_url[len("sqlite:///"):])
            db_path.parent.mkdir(parents=True, exist_ok=True)

        connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
        engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)

        # Cria tabelas (idempotente) — importa modelos com sys.path ja resolvido
        try:
            from app.db.base import Base
            import app.domains.invites.models  # noqa: F401
            try:
                import app.domains.users.models  # noqa: F401
            except ImportError:
                pass
            Base.metadata.create_all(bind=engine)
        except Exception:
            # Se os modelos nao estiverem acessiveis, continua sem create_all
            # (tabelas podem ja existir de um boot anterior)
            pass

        Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        return Session(), None

    except Exception as exc:
        return None, str(exc)
