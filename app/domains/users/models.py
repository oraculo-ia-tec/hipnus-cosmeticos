"""
models.py — Domínio Users
===========================
Modelo ORM do usuário da plataforma HIPNUS COSMÉTICOS.

Roles disponíveis (mapeados do JWT):
  super_admin  — acesso irrestrito (equipe Hipnus)
  admin        — administrador operacional
  b2b          — profissional / salão / distribuidor
  b2c          — consumidor final
  demo         — acesso público / somente leitura
"""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserRole(str, enum.Enum):
    super_admin = "super_admin"
    admin       = "admin"
    b2b         = "b2b"
    b2c         = "b2c"
    demo        = "demo"


class User(Base):
    """
    Tabela: users

    Armazena todos os usuários da plataforma.
    O campo `role` determina o nível de acesso e a experiência exibida.
    """
    __tablename__ = "users"

    id:           Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    name:         Mapped[str]      = mapped_column(String(120), nullable=False)
    username:     Mapped[str]      = mapped_column(String(60),  unique=True, index=True, nullable=False)
    email:        Mapped[str]      = mapped_column(String(180), unique=True, index=True, nullable=False)
    display_name: Mapped[str]      = mapped_column(String(120), nullable=True)
    hashed_password: Mapped[str]   = mapped_column(String(255), nullable=False)
    role:         Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False), default=UserRole.b2c, nullable=False
    )
    is_active:    Mapped[bool]     = mapped_column(Boolean, default=True,  nullable=False)
    is_verified:  Mapped[bool]     = mapped_column(Boolean, default=False, nullable=False)
    created_at:   Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at:   Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r} role={self.role}>"
