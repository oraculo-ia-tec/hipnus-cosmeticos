"""
Mixins reutilizáveis para os models SQLAlchemy.

`TimestampMixin` adiciona colunas de id, criação e atualização automática,
padronizando auditoria mínima em todas as entidades (requisito de governança).
"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Adiciona id (PK), created_at e updated_at a qualquer model."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
