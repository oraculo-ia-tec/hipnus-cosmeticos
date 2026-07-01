"""
parceiros.py — Models SQLAlchemy para tabelas `parceiros` e `app_configs`
==========================================================================
Substitui o DDL SQLite raw do user_db.py por models declarativos compatíveis
com qualquer banco suportado pelo SQLAlchemy (SQLite local e PostgreSQL/Supabase).

Vantagens sobre SQL raw:
  - Base.metadata.create_all() gera DDL correto por dialeto automaticamente
  - Sem AUTOINCREMENT (SQLite-only), sem ON CONFLICT manual
  - Tipo Text nativo para avatar_b64 (base64 pode ultrapassar 65k chars)
  - UniqueConstraint explícita garante upsert portável via ORM
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Parceiro(Base):
    """
    Tabela: parceiros

    Armazena parceiros B2B, admins e consumidores da plataforma.
    O campo avatar_b64 guarda a foto do usuário em formato data-URI base64
    (ex: data:image/jpeg;base64,...) — persiste entre sessões no banco.
    """
    __tablename__ = "parceiros"

    id:         Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    username:   Mapped[str | None]     = mapped_column(String(60),  unique=True,  nullable=True)
    nome:       Mapped[str]            = mapped_column(String(120), nullable=False)
    email:      Mapped[str]            = mapped_column(String(180), unique=True,  nullable=False, index=True)
    telefone:   Mapped[str | None]     = mapped_column(String(30),  nullable=True)
    empresa:    Mapped[str | None]     = mapped_column(String(120), nullable=True)
    cidade:     Mapped[str | None]     = mapped_column(String(80),  nullable=True)
    estado:     Mapped[str | None]     = mapped_column(String(2),   nullable=True)
    role:       Mapped[str]            = mapped_column(String(30),  nullable=False, default="b2b")
    senha_hash: Mapped[str]            = mapped_column(String(128), nullable=False)
    # Foto do usuário armazenada como data-URI base64 — persiste no banco
    avatar_b64: Mapped[str | None]     = mapped_column(Text,        nullable=True)
    bio:        Mapped[str | None]     = mapped_column(Text,        nullable=True)
    cpf_cnpj:   Mapped[str | None]     = mapped_column(String(14),  nullable=True)
    phone:      Mapped[str | None]     = mapped_column(String(30),  nullable=True)
    created_at: Mapped[datetime]       = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime]       = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Parceiro id={self.id} username={self.username!r} role={self.role}>"


class AppConfig(Base):
    """
    Tabela: app_configs

    Armazena configurações globais como chave-valor.
    Usado para persistir dados da Chiara (foto, nome, cargo, saudação)
    e outras configurações globais da plataforma.
    A foto da Chiara (chiara_foto_b64) é salva aqui em base64
    e persiste permanentemente no banco — não é perdida ao encerrar sessão.
    """
    __tablename__ = "app_configs"

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    chave:      Mapped[str]      = mapped_column(String(120), unique=True, nullable=False, index=True)
    valor:      Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<AppConfig chave={self.chave!r}>"
