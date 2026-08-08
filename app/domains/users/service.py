"""
service.py — Domínio Users
============================
Lógica de negócio: criação de usuários, autenticação e JWT.

As funções de hash e JWT foram movidas para app/skills/auth_skill.py.
Este módulo mantém os aliases para retrocompatibilidade e concentra
as operações de banco (CRUD).

Fluxo de login:
  1. Busca usuário por username.
  2. Verifica senha com bcrypt (via auth_skill.verify_password).
  3. Gera JWT contendo os campos do payload abaixo.

Payload JWT:
  id, name, username, email, display_name, role, is_active, is_verified
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.domains.users.models import User, UserRole
from app.domains.users.schemas import UserCreate
from app.skills.auth_skill import (
    create_token,
    decode_token,
    hash_password,
    verify_password,
)

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_token",
    "get_by_username",
    "get_by_email",
    "get_by_id",
    "create_user",
    "authenticate",
    "seed_super_admin",
]


def create_access_token(user: User, expires_minutes: int = 60 * 8) -> str:
    """
    Gera um JWT com o payload completo do usuário.
    Delega para auth_skill.create_token.
    """
    payload = {
        "sub":          str(user.id),
        "id":           user.id,
        "name":         user.name,
        "username":     user.username,
        "email":        user.email,
        "display_name": user.display_name,
        "role":         user.role.value,
        "is_active":    user.is_active,
        "is_verified":  user.is_verified,
    }
    return create_token(payload, expires_minutes=expires_minutes)


# ─── CRUD ─────────────────────────────────────────────────────────────────

def get_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username.lower()).first()


def get_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email.lower()).first()


def get_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, data: UserCreate) -> User:
    """
    Cria um novo usuário.
    Lança ValueError se username ou e-mail já existirem.
    """
    if get_by_username(db, data.username):
        raise ValueError(f"Username '{data.username}' já está em uso.")
    if get_by_email(db, data.email):
        raise ValueError(f"E-mail '{data.email}' já está cadastrado.")

    user = User(
        name=data.name,
        username=data.username.lower(),
        email=data.email.lower(),
        display_name=data.display_name,
        hashed_password=hash_password(data.password),
        role=data.role,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, username: str, password: str) -> Optional[User]:
    """
    Autentica usuário por username + senha.
    Retorna o User se válido e ativo, None caso contrário.
    """
    user = get_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


def seed_super_admin(db: Session) -> None:
    """
    Garante que o super_admin padrão exista no banco.
    Chamado no startup da aplicação.
    Credenciais definidas em settings (ADMIN_USERNAME / ADMIN_PASSWORD).
    """
    if get_by_username(db, settings.admin_username):
        return
    user = User(
        name=settings.admin_name,
        username=settings.admin_username.lower(),
        email=settings.admin_email,
        display_name="Administrador Hipnus",
        hashed_password=hash_password(settings.admin_password),
        role=UserRole.super_admin,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
