"""
invite_db.py — TÁLYA COSMÉTICOS
CRUD de tokens de convite via Supabase (tabela: invites)

API pública (inalterada):
  criar_invite_db(email, role, dias)   → str (token UUID)
  listar_invites_db()                  → list[dict]
  deletar_invite_db(token)             → None
  reativar_invite_db(token, dias)      → None
  validar_invite_db(token)             → dict | None
  marcar_invite_usado_db(token)        → None
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone


def _supa():
    from lib.supabase_client import get_supabase
    return get_supabase()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _exp_iso(dias: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=dias)).isoformat()


# ─── CRUD ─────────────────────────────────────────────────────────────────────

def criar_invite_db(email: str, role: str = "b2b", dias: int = 30) -> str:
    """Insere convite no Supabase e retorna o token UUID."""
    token = str(uuid.uuid4())
    _supa().table("invites").insert({
        "token":      token,
        "email":      email.lower().strip(),
        "role":       role,
        "created_by": "platform",
        "used":       False,
        "expires_at": _exp_iso(dias),
        "created_at": _now_iso(),
    }).execute()
    return token


def listar_invites_db() -> list[dict]:
    """Retorna todos os convites ordenados por criação desc."""
    res = (
        _supa().table("invites")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


def deletar_invite_db(token: str) -> None:
    """Remove convite pelo token."""
    _supa().table("invites").delete().eq("token", token).execute()


def reativar_invite_db(token: str, dias: int = 30) -> None:
    """Reativa convite expirado/usado estendendo o prazo."""
    _supa().table("invites").update({
        "used":       False,
        "used_at":    None,
        "expires_at": _exp_iso(dias),
    }).eq("token", token).execute()


def validar_invite_db(token: str) -> dict | None:
    """
    Retorna dict {token, email, role, expires_at} se válido,
    ou None se não encontrado, já usado ou expirado.
    """
    res = _supa().table("invites").select("*").eq("token", token).limit(1).execute()
    rows = res.data or []
    if not rows:
        return None

    data = rows[0]

    if data.get("used"):
        return None

    try:
        exp = datetime.fromisoformat(data["expires_at"])
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            return None
    except Exception:
        pass

    return {
        "token":      data["token"],
        "email":      data["email"],
        "role":       data.get("role", "b2b"),
        "expires_at": data["expires_at"],
    }


def marcar_invite_usado_db(token: str) -> None:
    """Marca convite como usado."""
    _supa().table("invites").update({
        "used":    True,
        "used_at": _now_iso(),
    }).eq("token", token).execute()

