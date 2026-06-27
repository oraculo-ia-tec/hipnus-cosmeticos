"""
init_db.py — Inicialização do banco de dados
==============================================
Garante que todas as tabelas existam antes de qualquer operação.
Deve ser chamado no startup do Streamlit (streamlit_app.py).

Lógica de resolução do DATABASE_URL (em ordem de prioridade):
  1. st.secrets["DATABASE_URL"]  (Streamlit Cloud)
  2. os.environ["DATABASE_URL"]  (VPS / Docker)
  3. settings.DATABASE_URL        (default do Pydantic: sqlite:///./data/hipnus.db)

Idempotente: só cria tabelas que ainda não existem, nunca destrói dados.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def _resolve_database_url() -> str:
    """
    Resolve o DATABASE_URL com prioridade:
      1. st.secrets (Streamlit Cloud)
      2. os.environ
      3. Pydantic settings (default)
    """
    # 1. Tenta st.secrets
    try:
        import streamlit as st
        val = st.secrets.get("DATABASE_URL") or st.secrets.get("default", {}).get("DATABASE_URL")
        if val:
            return val.strip().strip('"').strip("'")
    except Exception:
        pass

    # 2. Tenta os.environ
    val = os.environ.get("DATABASE_URL")
    if val:
        return val.strip()

    # 3. Default do Pydantic settings
    try:
        from app.core.config import settings
        return settings.DATABASE_URL
    except Exception:
        return "sqlite:///./data/hipnus.db"


def init_db() -> None:
    """
    Cria todas as tabelas registradas no metadata se ainda não existirem.

    1. Resolve DATABASE_URL (st.secrets > os.environ > settings default)
    2. Importa todos os models disponíveis (garante registro no Base.metadata)
    3. Cria o diretório do arquivo SQLite se não existir
    4. Executa create_all (idempotente)
    """
    try:
        db_url = _resolve_database_url()
        logger.info("[init_db] DATABASE_URL resolvido: %s", db_url[:40])

        # Importa Base e cria engine com a URL resolvida
        from sqlalchemy import create_engine
        from sqlalchemy.orm import DeclarativeBase

        # Importa Base do projeto
        from app.db.base import Base

        # Importa models para registrar no metadata (ordem importa)
        import app.domains.invites.models  # noqa: F401
        try:
            import app.domains.users.models    # noqa: F401
        except ImportError:
            pass
        try:
            import app.domains.partners.models  # noqa: F401
        except ImportError:
            pass
        try:
            import app.domains.catalog.models   # noqa: F401
        except ImportError:
            pass
        try:
            import app.domains.orders.models    # noqa: F401
        except ImportError:
            pass

        # Garante diretório para SQLite
        if db_url.startswith("sqlite:///"):
            db_path_str = db_url.replace("sqlite:///", "", 1)
            db_path = Path(db_path_str)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info("[init_db] Diretório SQLite: %s", db_path.parent.resolve())

        # Cria engine com a URL resolvida e executa create_all
        connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
        engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
        Base.metadata.create_all(bind=engine)
        logger.info("[init_db] Tabelas criadas/verificadas com sucesso.")

    except Exception as exc:
        logger.error("[init_db] Falha ao inicializar banco: %s", exc)
