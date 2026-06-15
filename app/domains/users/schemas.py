"""
schemas.py — Domínio Users
============================
Schemas Pydantic para serialização e validação de usuários.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator

from app.domains.users.models import UserRole


class UserCreate(BaseModel):
    name:         str
    username:     str
    email:        EmailStr
    display_name: Optional[str] = None
    password:     str
    role:         UserRole = UserRole.b2c

    @field_validator("username")
    @classmethod
    def username_lower(cls, v: str) -> str:
        return v.strip().lower()


class UserRead(BaseModel):
    id:           int
    name:         str
    username:     str
    email:        str
    display_name: Optional[str]
    role:         UserRole
    is_active:    bool
    is_verified:  bool
    created_at:   datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user:         UserRead


class LoginRequest(BaseModel):
    username: str
    password: str
