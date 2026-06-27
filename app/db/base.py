"""
Configuração do SQLAlchemy: engine, sessão e Base declarativa.

Suporta SQLite (local) e MySQL (produção Hostinger) de forma transparente
a partir de `settings.DATABASE_URL`.

Convenções:
- Todos os models herdam de `Base`.
- Toda tabela ganha automaticamente `id`, `created_at`, `updated_at` via
  o mixin `TimestampMixin` (definido em app/db/mixins.py).
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# SQLite exige connect_args específico para uso multi-thread no FastAPI.
_connect_args = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.debug,        # Pydantic v2: atributo em lowercase
    pool_pre_ping=True,
    connect_args=_connect_args,
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
