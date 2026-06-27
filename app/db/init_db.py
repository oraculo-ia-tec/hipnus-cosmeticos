"""
init_db.py — Inicialização do banco de dados
==============================================
Garante que todas as tabelas existam antes de qualquer operação.
Deve ser chamado no startup do Streamlit (streamlit_app.py) e da API (main.py).

Responsabilidades:
  - Importa todos os models para que o SQLAlchemy os registre no metadata
  - Garante que o diretório do SQLite exista (cria se necessário)
  - Executa Base.metadata.create_all(engine) de forma idempotente
    (só cria tabelas que ainda não existem, nunca destrói dados)

Uso:
  from app.db.init_db import init_db
  init_db()   # chame uma vez no startup

Seguro para chamar múltiplas vezes (idempotente).
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def init_db() -> None:
    """
    Cria todas as tabelas registradas no metadata se ainda não existirem.

    1. Importa todos os models (garante registro no Base.metadata)
    2. Cria o diretório do arquivo SQLite se não existir
    3. Executa create_all (idempotente)

    Não lança exceção em caso de falha — apenas loga o erro.
    Isso garante que o app suba mesmo com banco temporariamente indisponível.
    """
    try:
        # 1. Importa models para registrar no metadata
        from app.db.base import Base, engine
        import app.domains.invites.models  # noqa: F401
        import app.domains.users.models    # noqa: F401
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

        # 2. Garante diretorio para SQLite
        from app.core.config import settings
        db_url = settings.DATABASE_URL
        if db_url.startswith("sqlite:///"):
            # Extrai o caminho do arquivo: sqlite:///./data/hipnus.db -> ./data/hipnus.db
            db_path_str = db_url.replace("sqlite:///", "")
            db_path     = Path(db_path_str)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info("[init_db] Diretório SQLite: %s", db_path.parent.resolve())

        # 3. Cria tabelas (idempotente)
        Base.metadata.create_all(bind=engine)
        logger.info("[init_db] Tabelas criadas/verificadas com sucesso.")

    except Exception as exc:
        logger.error("[init_db] Falha ao inicializar banco: %s", exc)
