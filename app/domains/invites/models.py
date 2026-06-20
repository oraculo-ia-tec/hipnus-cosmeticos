"""
models.py — Domínio Invites
============================
Modelo ORM para convites de cadastro da plataforma HIPNUS COSMÉTICOS.

Fluxo:
  1. Admin/super_admin cria um convite para um e-mail com um role.
  2. O sistema gera um token UUID único e uma URL de cadastro.
  3. O e-mail é enviado via SMTP Hostinger com o link.
  4. O convidado acessa o link, preenche o cadastro e o token é marcado como usado.

Campos:
  token      — UUID v4 único, usado na URL de cadastro
  email      — destinatário do convite
  role       — perfil que o convidado terá após cadastro (b2b, admin, b2c)
  created_by — username do admin que gerou o convite
  used       — True quando o cadastro for concluído
  used_at    — timestamp do uso
  expires_at — 7 dias após criação
  created_at — timestamp de criação
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Invite(Base):
    """
    Tabela: invites

    Armazena convites de acesso gerados por administradores.
    Cada convite é vinculado a um e-mail específico e expira em 7 dias.
    """
    __tablename__ = "invites"

    id:         Mapped[int]            = mapped_column(Integer, primary_key=True, index=True)
    token:      Mapped[str]            = mapped_column(String(64),  unique=True, index=True, nullable=False)
    email:      Mapped[str]            = mapped_column(String(180), index=True,  nullable=False)
    role:       Mapped[str]            = mapped_column(String(30),  nullable=False, default="b2b")
    created_by: Mapped[str]            = mapped_column(String(60),  nullable=False, default="system")
    used:       Mapped[bool]           = mapped_column(Boolean, default=False, nullable=False)
    used_at:    Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime]       = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime]       = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<Invite id={self.id} email={self.email!r} role={self.role} used={self.used}>"
