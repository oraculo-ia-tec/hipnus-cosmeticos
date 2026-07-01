"""
init_db.py — Inicialização do banco de dados
==============================================
Garante que todas as tabelas existam antes de qualquer operação.
Deve ser chamado no startup do Streamlit (streamlit_app.py).

Lógica de resolução do DATABASE_URL (em ordem de prioridade):
  1. st.secrets["DATABASE_URL"]  (Streamlit Cloud)
  2. os.environ["DATABASE_URL"]  (VPS / Docker)
  3. settings.database_url       (default do Pydantic: sqlite:///./data/hipnus.db)

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
      3. Pydantic settings (default lowercase)
    """
    try:
        import streamlit as st
        val = st.secrets.get("DATABASE_URL") or st.secrets.get("default", {}).get("DATABASE_URL")
        if val:
            return val.strip().strip('"').strip("'")
    except Exception:
        pass

    val = os.environ.get("DATABASE_URL")
    if val:
        return val.strip()

    try:
        from app.core.config import settings
        return settings.database_url
    except Exception:
        return "sqlite:///./data/hipnus.db"


def init_db() -> None:
    """
    Cria todas as tabelas registradas no metadata se ainda não existirem.

    1. Resolve DATABASE_URL (st.secrets > os.environ > settings default)
    2. Importa todos os models disponíveis (garante registro no Base.metadata)
    3. Cria o diretório do arquivo SQLite se não existir
    4. Executa create_all (idempotente)

    Tabelas gerenciadas:
      - invites         (app.domains.invites.models)
      - users           (app.domains.users.models)
      - parceiros       (app.domains.partners.models.parceiros)  ← avatar_b64
      - app_configs     (app.domains.partners.models.parceiros)  ← foto Chiara
      - partners, catalog, orders (se disponíveis)
    """
    try:
        db_url = _resolve_database_url()
        logger.info("[init_db] DATABASE_URL resolvido: %s", db_url[:40])

        from sqlalchemy import create_engine
        from app.db.base import Base

        # ─ Models obrigatórios ──────────────────────────────────────────────
        import app.domains.invites.models  # noqa: F401

        # Parceiros e AppConfig (imagens do usuário e da Chiara)
        import app.domains.partners.models.parceiros  # noqa: F401

        # ─ Models opcionais ───────────────────────────────────────────────
        for _mod in [
            "app.domains.users.models",
            "app.domains.catalog.models",
            "app.domains.orders.models",
        ]:
            try:
                __import__(_mod)
            except ImportError:
                pass

        # Garante diretório para SQLite
        if db_url.startswith("sqlite:///"):
            db_path_str = db_url.replace("sqlite:///", "", 1)
            db_path = Path(db_path_str)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info("[init_db] Diretório SQLite: %s", db_path.parent.resolve())

        connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
        engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
        Base.metadata.create_all(bind=engine)
        logger.info("[init_db] Tabelas criadas/verificadas com sucesso.")

    except Exception as exc:
        logger.error("[init_db] Falha ao inicializar banco: %s", exc)
