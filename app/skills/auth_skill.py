"""
auth_skill.py — TÁLYA COSMÉTICOS
====================================
Skill de Autenticação: módulo compartilhado entre backend e frontend.

Responsabilidades:
  - Hash e verificação de senha via bcrypt (passlib)
  - Geração e decodificação de JWT (jose)
  - Normalização de roles (aliases e variações aceitas)

Substitui:
  - app/domains/users/service.py  (hash_password, verify_password,
                                   create_access_token, decode_token)
  - frontend/lib/tokens.py        (JWT decode)
  - frontend/lib/user_db.py       (_hash_senha via SHA-256 — inseguro)

Uso no backend:
    from app.skills.auth_skill import hash_password, verify_password, create_token, decode_token

Uso no frontend (Streamlit):
    from app.skills.auth_skill import verify_password, decode_token, normalize_role
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# ─── Contexto bcrypt ─────────────────────────────────────────────────────────
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Gera hash bcrypt de uma senha em texto plano."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verifica senha contra hash.

    Suporta:
    - bcrypt (padrão atual — hashes começam com '$2b$')
    - SHA-256 legado (hashes hexadecimais de 64 chars — criados pelo user_db.py anterior)
    - SHA-256 legado com prefixo 'sha256:' (formato intermediário)

    A compatibilidade com SHA-256 permite migrar gradualmente usuários
    antigos sem forçar reset de senhas.
    """
    import hashlib as _hashlib

    # Verificação de hash legado — SOMENTE para leitura/comparação de hashes
    # existentes no banco. Novos hashes são sempre bcrypt. SHA-256 sozinho é
    # fraco para armazenamento, mas é seguro aqui pois apenas compara — nunca armazena.
    if hashed.startswith("sha256:"):
        legacy_hash = _hashlib.sha256(plain.encode("utf-8")).hexdigest()  # nosec B324
        return legacy_hash == hashed[len("sha256:"):]

    # Bcrypt começa com '$2b$' (passlib também aceita '$2a$' e '$2y$')
    if hashed.startswith("$2"):
        return _pwd_context.verify(plain, hashed)

    # Fallback: hash hexadecimal puro (SHA-256 sem prefixo — legado user_db.py)
    if len(hashed) == 64 and all(c in "0123456789abcdef" for c in hashed):
        legacy_hash = _hashlib.sha256(plain.encode("utf-8")).hexdigest()  # nosec B324
        return legacy_hash == hashed

    # Formato desconhecido — nega por segurança
    return False


def rehash_needed(hashed: str) -> bool:
    """Retorna True se o hash legado (SHA-256) precisa ser migrado para bcrypt."""
    return hashed.startswith("sha256:")


# ─── JWT ─────────────────────────────────────────────────────────────────────

def create_token(payload_extra: dict[str, Any], expires_minutes: int | None = None) -> str:
    """
    Gera JWT assinado com HS256.

    Args:
        payload_extra: campos adicionais a incluir no token (id, name, role, etc.)
        expires_minutes: TTL em minutos (padrão: settings.access_token_minutes)

    Retorna: string JWT.
    """
    minutes = expires_minutes if expires_minutes is not None else settings.access_token_minutes
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload = {**payload_extra, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> dict:
    """
    Decodifica e valida JWT.

    Lança jose.JWTError se o token for inválido ou expirado.
    """
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])


# ─── Normalização de roles ────────────────────────────────────────────────────

_ROLE_ALIASES: dict[str, str] = {
    "super user":   "super_admin",
    "superuser":    "super_admin",
    "super-admin":  "super_admin",
    "super admin":  "super_admin",
    "superadmin":   "super_admin",
    "super_admin":  "super_admin",
    "admin":        "admin",
    "b2b":          "b2b",
    "profissional": "b2b",
    "salao":        "b2b",
    "distribuidor": "b2b",
    "revendedor":   "b2b",
    "b2c":          "b2c",
    "cliente":      "b2c",
    "consumer":     "b2c",
    "demo":         "demo",
}

VALID_ROLES = frozenset({"super_admin", "admin", "b2b", "b2c", "demo"})


def normalize_role(role: str | None) -> str:
    """
    Normaliza uma string de role para um dos valores canônicos.

    Valores canônicos: super_admin | admin | b2b | b2c | demo
    Qualquer entrada desconhecida retorna 'demo' (menor privilégio).
    """
    normalized = (role or "demo").strip().lower()
    return _ROLE_ALIASES.get(normalized, "demo")
