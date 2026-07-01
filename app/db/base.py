"""
Configuração do SQLAlchemy: engine, sessão e Base declarativa.

Suporta SQLite (local) e PostgreSQL/Supabase (produção) de forma transparente
a partir de `settings.DATABASE_URL` ou `st.secrets["DATABASE_URL"]`.

Convenções:
- Todos os models herdam de `Base`.
- Toda tabela ganha automaticamente `id`, `created_at`, `updated_at` via
  o mixin `TimestampMixin` (definido em app/db/mixins.py).

Pool para Supabase (PgBouncer, porta 6543):
- pool_size=5        — conexões persistentes mantidas abertas
- max_overflow=10    — conexões extras em pico de carga
- pool_timeout=30    — tempo máximo de espera por conexão livre (seg)
- pool_recycle=1800  — recicla conexões a cada 30 min (evita idle timeout)
- pool_pre_ping=True — valida conexão antes de usar (evita conexão morta)
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


def _build_engine_kwargs(db_url: str) -> dict:
    """
    Retorna kwargs adequados ao banco detectado pela URL.
    - SQLite: connect_args com check_same_thread=False, sem pool configurado
    - PostgreSQL/Supabase: pool otimizado para PgBouncer (porta 6543)
    """
    if db_url.startswith("sqlite"):
        return {
            "connect_args": {"check_same_thread": False},
            "pool_pre_ping": True,
        }
    # PostgreSQL — Supabase Pooler (PgBouncer transaction mode)
    return {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,
        "pool_pre_ping": True,
    }


engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.debug,
    **_build_engine_kwargs(settings.DATABASE_URL),
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """Base declarativa para todos os models do projeto."""


def get_db() -> Generator:
    """
    Dependência FastAPI que fornece uma sessão de banco por request.

    Garante fechamento da sessão ao final, mesmo em caso de exceção.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
