"""
schemas.py — Domínio Invites
==============================
Schemas Pydantic para validação e serialização dos convites.

Schemas:
  InviteCreate  — entrada para criação de convite (POST /invites/)
  InviteOut     — saída pública de um convite (resposta da API)
  InviteCreated — resposta após criação bem-sucedida, inclui signup_url
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr


class InviteCreate(BaseModel):
    """
    Payload para criação de um novo convite.

    Campos:
      email — e-mail do destinatário (obrigatório, validado como e-mail)
      role  — perfil do convidado: b2b | b2c | admin (padrão: b2b)
    """
    email: EmailStr
    role:  Literal["b2b", "b2c", "admin"] = "b2b"


class InviteOut(BaseModel):
    """
    Representação pública de um convite.
    Retornado em listagens e detalhes.
    """
    id:         int
    token:      str
    email:      str
    role:       str
    created_by: str
    used:       bool
    used_at:    datetime | None
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class InviteCreated(InviteOut):
    """
    Resposta estendida após criação, inclui a URL de cadastro e
    confirmação de envio de e-mail.

    Campos extras:
      signup_url   — link completo para o convidado se cadastrar
      email_sent   — True se o e-mail foi enviado com sucesso
    """
    signup_url: str
    email_sent: bool
