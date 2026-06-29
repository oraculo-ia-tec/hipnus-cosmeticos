"""
invite_db.py — HIPNUS COSMÉTICOS
CRUD de tokens de convite em SQLite (tabela: invites)

Funções públicas:
  criar_invite_db(email, role, dias)       → str (token UUID)
  listar_invites_db()                      → list[dict]
  deletar_invite_db(token)                 → None
  reativar_invite_db(token, dias)          → None
  validar_invite_db(token)                 → dict | None   ← NOVO
  marcar_invite_usado_db(token)            → None           ← NOVO
"""
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "hipnus.db"
_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def _ensure_table() -> None:
    with _conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS invites (
                token      TEXT PRIMARY KEY,
                email      TEXT NOT NULL,
                role       TEXT NOT NULL DEFAULT 'b2b',
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used       INTEGER NOT NULL DEFAULT 0,
                used_at    TEXT
            )
        """)
        # Migrações seguras (colunas opcionais adicionadas em versões anteriores)
        for col, definition in [
            ("role",    "TEXT NOT NULL DEFAULT 'b2b'"),
            ("used_at", "TEXT"),
        ]:
            try:
                con.execute(f"ALTER TABLE invites ADD COLUMN {col} {definition}")
            except sqlite3.OperationalError:
                pass  # já existe


_ensure_table()


def criar_invite_db(email: str, role: str = "b2b", dias: int = 30) -> str:
    """Cria um token de convite único e retorna o token."""
    token = str(uuid.uuid4())
    now   = datetime.now(timezone.utc)
    exp   = now + timedelta(days=dias)
    with _conn() as con:
        con.execute(
            "INSERT INTO invites (token, email, role, created_at, expires_at, used) "
            "VALUES (?, ?, ?, ?, ?, 0)",
            (token, email.lower().strip(), role, now.isoformat(), exp.isoformat()),
        )
    return token


def listar_invites_db() -> list[dict]:
    """Retorna todos os convites ordenados por data de criação desc."""
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM invites ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def deletar_invite_db(token: str) -> None:
    """Remove um convite pelo token."""
    with _conn() as con:
        con.execute("DELETE FROM invites WHERE token = ?", (token,))


def reativar_invite_db(token: str, dias: int = 30) -> None:
    """Reativa um convite usado, estendendo o prazo."""
    exp = (datetime.now(timezone.utc) + timedelta(days=dias)).isoformat()
    with _conn() as con:
        con.execute(
            "UPDATE invites SET used = 0, used_at = NULL, expires_at = ? WHERE token = ?",
            (exp, token),
        )


def validar_invite_db(token: str) -> dict | None:
    """
    Valida um token de convite.

    Retorna dict com {token, email, role, expires_at} se válido,
    ou None se:
      - Token não encontrado
      - Já foi usado (used == 1)
      - Expirou (expires_at < agora)
    """
    with _conn() as con:
        row = con.execute(
            "SELECT * FROM invites WHERE token = ?", (token,)
        ).fetchone()

    if not row:
        return None

    data = dict(row)

    if data.get("used", 0):
        return None

    try:
        exp = datetime.fromisoformat(data["expires_at"])
        # Garante timezone-aware para comparação
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            return None
    except Exception:
        pass  # Se não conseguir parsear, deixa passar

    return {
        "token":      data["token"],
        "email":      data["email"],
        "role":       data.get("role", "b2b"),
        "expires_at": data["expires_at"],
    }


def marcar_invite_usado_db(token: str) -> None:
    """
    Marca o convite como utilizado.
    Chamado imediatamente após o cadastro ser concluído com sucesso.
    """
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as con:
        con.execute(
            "UPDATE invites SET used = 1, used_at = ? WHERE token = ?",
            (now, token),
        )
