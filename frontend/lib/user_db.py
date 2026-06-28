"""
user_db.py — HIPNUS COSMÉTICOS
================================
Camada de acesso ao banco para o domínio de Usuários / Parceiros.

Tabela `parceiros`:
  id, username, nome, email, telefone, empresa, cidade, estado,
  role, senha_hash, avatar_b64 (TEXT base64), bio, created_at, updated_at

Funciona standalone (sem FastAPI).
"""
from __future__ import annotations

import base64
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT     = Path(__file__).resolve().parents[2]
_FRONTEND = Path(__file__).resolve().parents[1]
for _p in [str(_ROOT), str(_FRONTEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from lib.db_utils import get_db_session  # noqa: E402
from sqlalchemy import text              # noqa: E402


CREATE_PARCEIROS = """
CREATE TABLE IF NOT EXISTS parceiros (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    VARCHAR(60)  UNIQUE,
    nome        VARCHAR(120) NOT NULL,
    email       VARCHAR(180) NOT NULL UNIQUE,
    telefone    VARCHAR(30),
    empresa     VARCHAR(120),
    cidade      VARCHAR(80),
    estado      VARCHAR(2),
    role        VARCHAR(30)  NOT NULL DEFAULT 'b2b',
    senha_hash  VARCHAR(128) NOT NULL,
    avatar_b64  TEXT,
    bio         TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""


def _hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def _ensure_table(db) -> None:
    try:
        db.execute(text(CREATE_PARCEIROS))
        db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass


def _ensure_column(db, column: str, col_type: str = "VARCHAR(60)") -> None:
    """Adiciona coluna na tabela parceiros se ainda não existir (SQLite-safe)."""
    try:
        db.execute(text(f"ALTER TABLE parceiros ADD COLUMN {column} {col_type}"))
        db.commit()
    except Exception:
        # Coluna já existe ou erro ignorável
        try:
            db.rollback()
        except Exception:
            pass


# ─── Listar parceiros ─────────────────────────────────────────────────────────────
def listar_parceiros() -> list[dict]:
    """Retorna todos os parceiros cadastrados (para painel admin)."""
    db, _ = get_db_session()
    if not db:
        return []
    try:
        _ensure_table(db)
        rows = db.execute(text(
            "SELECT id, username, nome, email, role, empresa, cidade, estado, "
            "telefone, created_at, updated_at FROM parceiros ORDER BY created_at DESC"
        )).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception:
        return []
    finally:
        db.close()


# ─── Criar parceiro ──────────────────────────────────────────────────────────────────
def criar_parceiro(
    nome: str,
    email: str,
    senha: str,
    role: str = "b2b",
    username: str | None = None,
    telefone: str = "",
    empresa: str = "",
    cidade: str = "",
    estado: str = "",
    avatar_b64: str | None = None,
) -> tuple[bool, str]:
    """Insere novo parceiro. Retorna (ok, mensagem)."""
    db, err = get_db_session()
    if not db:
        return False, f"Banco indisponível: {err}"
    try:
        _ensure_table(db)
        uname      = (username or email.split("@")[0]).strip().lower()
        senha_hash = _hash_senha(senha)
        db.execute(text("""
            INSERT INTO parceiros
                (username, nome, email, telefone, empresa, cidade, estado,
                 role, senha_hash, avatar_b64)
            VALUES
                (:username, :nome, :email, :telefone, :empresa, :cidade, :estado,
                 :role, :senha_hash, :avatar_b64)
        """), {
            "username":   uname,
            "nome":       nome,
            "email":      email.lower().strip(),
            "telefone":   telefone,
            "empresa":    empresa,
            "cidade":     cidade,
            "estado":     estado,
            "role":       role,
            "senha_hash": senha_hash,
            "avatar_b64": avatar_b64,
        })
        db.commit()
        return True, "Parceiro criado com sucesso!"
    except Exception as exc:
        db.rollback()
        msg = str(exc)
        if "UNIQUE" in msg.upper():
            if "email" in msg:
                return False, "E-mail já cadastrado."
            if "username" in msg:
                return False, "Nome de usuário já em uso. Escolha outro."
        return False, msg
    finally:
        db.close()


# ─── Alias: cadastrar_parceiro (compat) ───────────────────────────────────────
def cadastrar_parceiro(
    nome: str,
    email: str,
    senha: str,
    perfil: str = "b2b",
    cidade: str = "",
    estado: str = "",
    **kwargs,
) -> None:
    """Alias de criar_parceiro() para compatibilidade com as páginas.
    Lança Exception em caso de erro para que o form exiba st.error().
    """
    ok, msg = criar_parceiro(
        nome=nome, email=email, senha=senha,
        role=perfil, cidade=cidade, estado=estado, **kwargs,
    )
    if not ok:
        raise ValueError(msg)


# ─── Deletar parceiro ───────────────────────────────────────────────────────────────
def deletar_parceiro(email: str) -> None:
    """Remove parceiro pelo e-mail. Lança Exception em caso de erro."""
    db, err = get_db_session()
    if not db:
        raise RuntimeError(f"Banco indisponível: {err}")
    try:
        _ensure_table(db)
        db.execute(
            text("DELETE FROM parceiros WHERE email = :email"),
            {"email": email.lower().strip()},
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        raise exc
    finally:
        db.close()


# ─── Buscar parceiro por email ───────────────────────────────────────────────────────────
def buscar_por_email(email: str) -> dict | None:
    db, _ = get_db_session()
    if not db:
        return None
    try:
        _ensure_table(db)
        row = db.execute(
            text("SELECT * FROM parceiros WHERE email = :email"),
            {"email": email.lower().strip()},
        ).fetchone()
        return dict(row._mapping) if row else None
    except Exception:
        return None
    finally:
        db.close()


# ─── Autenticar parceiro ──────────────────────────────────────────────────────────────────
def autenticar_parceiro(email: str, senha: str) -> dict | None:
    """Valida e-mail + senha. Retorna dados do parceiro ou None."""
    parceiro = buscar_por_email(email)
    if not parceiro:
        return None
    if parceiro.get("senha_hash") != _hash_senha(senha):
        return None
    return parceiro


# ─── Atualizar perfil ────────────────────────────────────────────────────────────────────
def atualizar_perfil(
    email: str,
    nome: str | None = None,
    username: str | None = None,
    telefone: str | None = None,
    empresa: str | None = None,
    cidade: str | None = None,
    estado: str | None = None,
    bio: str | None = None,
    avatar_b64: str | None = None,
) -> tuple[bool, str]:
    db, err = get_db_session()
    if not db:
        return False, f"Banco indisponível: {err}"
    try:
        _ensure_table(db)
        sets, params = [], {"email": email.lower().strip()}
        if nome       is not None: sets.append("nome = :nome");             params["nome"]       = nome
        if username   is not None: sets.append("username = :username");     params["username"]   = username.lower().strip()
        if telefone   is not None: sets.append("telefone = :telefone");     params["telefone"]   = telefone
        if empresa    is not None: sets.append("empresa = :empresa");       params["empresa"]    = empresa
        if cidade     is not None: sets.append("cidade = :cidade");         params["cidade"]     = cidade
        if estado     is not None: sets.append("estado = :estado");         params["estado"]     = estado
        if bio        is not None: sets.append("bio = :bio");               params["bio"]        = bio
        if avatar_b64 is not None: sets.append("avatar_b64 = :avatar_b64"); params["avatar_b64"] = avatar_b64
        if not sets:
            return True, "Nada a atualizar."
        sets.append("updated_at = :updated_at")
        params["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        db.execute(text(f"UPDATE parceiros SET {', '.join(sets)} WHERE email = :email"), params)
        db.commit()
        return True, "Perfil atualizado!"
    except Exception as exc:
        db.rollback()
        return False, str(exc)
    finally:
        db.close()


# ─── Persistir CPF/CNPJ e telefone vindos do checkout ─────────────────────────
def atualizar_cpf_phone(
    email: str,
    cpf_cnpj: str | None = None,
    phone: str | None = None,
) -> tuple[bool, str]:
    """
    Persiste CPF/CNPJ e telefone no registro do parceiro após confirmação no checkout.

    - Garante que as colunas `cpf_cnpj` e `phone` existem na tabela (cria via
      ALTER TABLE se necessário — seguro para SQLite).
    - Nunca sobrescreve campos de login (senha_hash, role, email) — apenas
      enriquece dados complementares do perfil.
    - Silencioso em caso de banco indisponível (não bloqueia o checkout).
    """
    if not email:
        return False, "E-mail ausente."
    db, err = get_db_session()
    if not db:
        return False, f"Banco indisponível: {err}"
    try:
        _ensure_table(db)
        # Garante que as colunas extras existem (idempotente)
        _ensure_column(db, "cpf_cnpj", "VARCHAR(14)")
        _ensure_column(db, "phone",    "VARCHAR(30)")

        sets, params = [], {"email": email.lower().strip()}
        if cpf_cnpj:
            sets.append("cpf_cnpj = :cpf_cnpj")
            params["cpf_cnpj"] = cpf_cnpj
        if phone:
            sets.append("phone = :phone")
            params["phone"] = phone
        if not sets:
            return True, "Nada a persistir."
        sets.append("updated_at = :updated_at")
        params["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        db.execute(
            text(f"UPDATE parceiros SET {', '.join(sets)} WHERE email = :email"),
            params,
        )
        db.commit()
        return True, "CPF/CNPJ e telefone atualizados no banco."
    except Exception as exc:
        try:
            db.rollback()
        except Exception:
            pass
        return False, str(exc)
    finally:
        db.close()


# ─── Alterar senha ──────────────────────────────────────────────────────────────────────
def alterar_senha(email: str, senha_atual: str, nova_senha: str) -> tuple[bool, str]:
    parceiro = autenticar_parceiro(email, senha_atual)
    if not parceiro:
        return False, "Senha atual incorreta."
    db, err = get_db_session()
    if not db:
        return False, f"Banco indisponível: {err}"
    try:
        db.execute(
            text("UPDATE parceiros SET senha_hash = :h, updated_at = :now WHERE email = :email"),
            {"h": _hash_senha(nova_senha), "now": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), "email": email.lower()},
        )
        db.commit()
        return True, "Senha alterada com sucesso!"
    except Exception as exc:
        db.rollback()
        return False, str(exc)
    finally:
        db.close()


# ─── Encode/decode avatar ──────────────────────────────────────────────────────────────────
def image_to_b64(file_bytes: bytes, mime: str = "image/jpeg") -> str:
    b64 = base64.b64encode(file_bytes).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def b64_to_html_img(b64_data_uri: str, size: int = 48, cls: str = "") -> str:
    return (
        f'<img src="{b64_data_uri}" '
        f'style="width:{size}px;height:{size}px;border-radius:50%;'
        f'object-fit:cover;border:2px solid rgba(255,255,255,.4);" '
        f'class="{cls}" />'
    )
