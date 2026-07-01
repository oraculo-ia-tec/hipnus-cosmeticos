"""
user_db.py — HIPNUS COSMÉTICOS
================================
Camada de acesso ao banco para o domínio de Usuários / Parceiros.

Tabela `parceiros`:
  id, username, nome, email, telefone, empresa, cidade, estado,
  role, senha_hash, avatar_b64 (Text base64-datauri), bio,
  cpf_cnpj, phone, created_at, updated_at

Tabela `app_configs`  (chave-valor global — usada para Chiara e config IA)
  id, chave, valor, updated_at
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


def _hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def _ensure_tables(db) -> None:
    try:
        from app.db.base import Base
        import app.domains.partners.models.parceiros  # noqa: F401
        Base.metadata.create_all(bind=db.get_bind())
    except Exception:
        pass


# ─── app_configs: chave-valor global ──────────────────────────────────────────────────────────────────────
def set_app_config(chave: str, valor: str) -> bool:
    db, err = get_db_session()
    if not db:
        return False
    try:
        _ensure_tables(db)
        from app.domains.partners.models.parceiros import AppConfig
        now = datetime.now(timezone.utc)
        obj = db.query(AppConfig).filter(AppConfig.chave == chave).first()
        if obj:
            obj.valor      = valor
            obj.updated_at = now
        else:
            obj = AppConfig(chave=chave, valor=valor, updated_at=now)
            db.add(obj)
        db.commit()
        return True
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        return False
    finally:
        db.close()


def get_app_config(chave: str) -> str | None:
    db, _ = get_db_session()
    if not db:
        return None
    try:
        _ensure_tables(db)
        from app.domains.partners.models.parceiros import AppConfig
        obj = db.query(AppConfig).filter(AppConfig.chave == chave).first()
        return obj.valor if obj else None
    except Exception:
        return None
    finally:
        db.close()


# ─── Foto da Chiara (IA Consultora) ────────────────────────────────────────────────────────────────────
def salvar_foto_chiara(b64: str, mime: str = "image/jpeg") -> bool:
    ok1 = set_app_config("chiara_foto_b64",  b64)
    ok2 = set_app_config("chiara_foto_mime", mime)
    return ok1 and ok2


def carregar_foto_chiara() -> tuple[str, str]:
    b64  = get_app_config("chiara_foto_b64")  or ""
    mime = get_app_config("chiara_foto_mime") or "image/jpeg"
    return b64, mime


def salvar_nome_chiara(nome: str, cargo: str = "") -> bool:
    ok1 = set_app_config("chiara_nome",  nome)
    ok2 = set_app_config("chiara_cargo", cargo) if cargo else True
    return ok1 and ok2


def carregar_config_chiara() -> dict:
    return {
        "nome":      get_app_config("chiara_nome")      or "Chiara",
        "cargo":     get_app_config("chiara_cargo")     or "Terapeuta Capilar Digital · Embaixadora HIPNUS",
        "foto_b64":  get_app_config("chiara_foto_b64")  or "",
        "foto_mime": get_app_config("chiara_foto_mime") or "image/jpeg",
        "saudacao":  get_app_config("chiara_saudacao")  or "",
    }


# ─── Listar parceiros ───────────────────────────────────────────────────────────────────────────────────────
def listar_parceiros() -> list[dict]:
    """Retorna todos os parceiros cadastrados (para painel admin)."""
    db, _ = get_db_session()
    if not db:
        return []
    try:
        _ensure_tables(db)
        from app.domains.partners.models.parceiros import Parceiro
        rows = (
            db.query(
                Parceiro.id, Parceiro.username, Parceiro.nome, Parceiro.email,
                Parceiro.role, Parceiro.empresa, Parceiro.cidade, Parceiro.estado,
                Parceiro.telefone, Parceiro.created_at, Parceiro.updated_at,
            )
            .order_by(Parceiro.created_at.desc())
            .all()
        )
        cols = ["id","username","nome","email","role","empresa","cidade","estado","telefone","created_at","updated_at"]
        return [dict(zip(cols, r)) for r in rows]
    except Exception:
        return []
    finally:
        db.close()


# ─── Criar parceiro ──────────────────────────────────────────────────────────────────────────────────────────
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
        _ensure_tables(db)
        from app.domains.partners.models.parceiros import Parceiro
        uname = (username or email.split("@")[0]).strip().lower()
        parceiro = Parceiro(
            username=uname,
            nome=nome,
            email=email.lower().strip(),
            telefone=telefone or None,
            empresa=empresa or None,
            cidade=cidade or None,
            estado=estado or None,
            role=role,
            senha_hash=_hash_senha(senha),
            avatar_b64=avatar_b64,
        )
        db.add(parceiro)
        db.commit()
        return True, "Parceiro criado com sucesso!"
    except Exception as exc:
        try:
            db.rollback()
        except Exception:
            pass
        msg = str(exc)
        if "unique" in msg.lower() or "duplicate" in msg.lower():
            if "email" in msg.lower():
                return False, "E-mail já cadastrado."
            if "username" in msg.lower():
                return False, "Nome de usuário já em uso. Escolha outro."
        return False, msg
    finally:
        db.close()


# ─── Alias: cadastrar_parceiro (compat) ────────────────────────────────────────────────────────────────────────────────
def cadastrar_parceiro(
    nome: str,
    email: str,
    senha: str,
    perfil: str = "b2b",
    cidade: str = "",
    estado: str = "",
    **kwargs,
) -> None:
    ok, msg = criar_parceiro(
        nome=nome, email=email, senha=senha,
        role=perfil, cidade=cidade, estado=estado, **kwargs,
    )
    if not ok:
        raise ValueError(msg)


# ─── Deletar parceiro ──────────────────────────────────────────────────────────────────────────────────────────
def deletar_parceiro(email: str) -> None:
    db, err = get_db_session()
    if not db:
        raise RuntimeError(f"Banco indisponível: {err}")
    try:
        _ensure_tables(db)
        from app.domains.partners.models.parceiros import Parceiro
        db.query(Parceiro).filter(
            Parceiro.email == email.lower().strip()
        ).delete(synchronize_session=False)
        db.commit()
    except Exception as exc:
        try:
            db.rollback()
        except Exception:
            pass
        raise exc
    finally:
        db.close()


# ─── Buscar parceiro por email ───────────────────────────────────────────────────────────────────────────────────────────
def buscar_por_email(email: str) -> dict | None:
    db, _ = get_db_session()
    if not db:
        return None
    try:
        _ensure_tables(db)
        from app.domains.partners.models.parceiros import Parceiro
        obj = db.query(Parceiro).filter(
            Parceiro.email == email.lower().strip()
        ).first()
        if not obj:
            return None
        return {
            c.name: getattr(obj, c.name)
            for c in obj.__table__.columns
        }
    except Exception:
        return None
    finally:
        db.close()


# ─── Autenticar parceiro ──────────────────────────────────────────────────────────────────────────────────────────────
def autenticar_parceiro(email: str, senha: str) -> dict | None:
    parceiro = buscar_por_email(email)
    if not parceiro:
        return None
    if parceiro.get("senha_hash") != _hash_senha(senha):
        return None
    return parceiro


# ─── Atualizar perfil (inclui avatar_b64) ────────────────────────────────────────────────────────────────────────────
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
        _ensure_tables(db)
        from app.domains.partners.models.parceiros import Parceiro
        obj = db.query(Parceiro).filter(
            Parceiro.email == email.lower().strip()
        ).first()
        if not obj:
            return False, "Parceiro não encontrado."
        if nome       is not None: obj.nome       = nome
        if username   is not None: obj.username   = username.lower().strip()
        if telefone   is not None: obj.telefone   = telefone
        if empresa    is not None: obj.empresa    = empresa
        if cidade     is not None: obj.cidade     = cidade
        if estado     is not None: obj.estado     = estado
        if bio        is not None: obj.bio        = bio
        if avatar_b64 is not None: obj.avatar_b64 = avatar_b64
        obj.updated_at = datetime.now(timezone.utc)
        db.commit()
        return True, "Perfil atualizado!"
    except Exception as exc:
        try:
            db.rollback()
        except Exception:
            pass
        return False, str(exc)
    finally:
        db.close()


# ─── Persistir CPF/CNPJ e telefone vindos do checkout ──────────────────────────────────────────────────────────────────
def atualizar_cpf_phone(
    email: str,
    cpf_cnpj: str | None = None,
    phone: str | None = None,
) -> tuple[bool, str]:
    if not email:
        return False, "E-mail ausente."
    db, err = get_db_session()
    if not db:
        return False, f"Banco indisponível: {err}"
    try:
        _ensure_tables(db)
        from app.domains.partners.models.parceiros import Parceiro
        obj = db.query(Parceiro).filter(
            Parceiro.email == email.lower().strip()
        ).first()
        if not obj:
            return False, "Parceiro não encontrado."
        if cpf_cnpj: obj.cpf_cnpj = cpf_cnpj
        if phone:    obj.phone    = phone
        obj.updated_at = datetime.now(timezone.utc)
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


# ─── Alterar senha ────────────────────────────────────────────────────────────────────────────────────────────────────────
def alterar_senha(email: str, senha_atual: str, nova_senha: str) -> tuple[bool, str]:
    parceiro = autenticar_parceiro(email, senha_atual)
    if not parceiro:
        return False, "Senha atual incorreta."
    db, err = get_db_session()
    if not db:
        return False, f"Banco indisponível: {err}"
    try:
        from app.domains.partners.models.parceiros import Parceiro
        obj = db.query(Parceiro).filter(
            Parceiro.email == email.lower()
        ).first()
        if not obj:
            return False, "Parceiro não encontrado."
        obj.senha_hash = _hash_senha(nova_senha)
        obj.updated_at = datetime.now(timezone.utc)
        db.commit()
        return True, "Senha alterada com sucesso!"
    except Exception as exc:
        try:
            db.rollback()
        except Exception:
            pass
        return False, str(exc)
    finally:
        db.close()


# ─── Encode/decode avatar ──────────────────────────────────────────────────────────────────────────────────────────────────
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
