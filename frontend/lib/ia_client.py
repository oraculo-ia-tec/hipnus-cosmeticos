"""
ia_client.py — HIPNUS COSMÉTICOS
====================================
Adaptador entre a página IA Consultora e o motor ia_consultora.py.
Expõe stream_ia() (gerador para st.write_stream) e consultar_ia() (string completa).

Atualização: injeta produtos do banco no contexto da IA para que a
catalog_llm_skill funcione com dados reais filtrados por perfil.
"""
from __future__ import annotations
import sys
from pathlib import Path

_ROOT     = Path(__file__).resolve().parents[2]
_FRONTEND = Path(__file__).resolve().parents[1]
for _p in [str(_ROOT), str(_FRONTEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from lib.ia_consultora import chat_stream, build_context  # noqa: E402


def _get_usuario_dict(usuario_override: dict | None = None) -> dict | None:
    """
    Monta o dict de usuário a partir do session_state.
    session_state["usuario"] é uma STRING (login/username) — não um dict.
    Os campos reais ficam em: nome, perfil, email, display_name.
    """
    if usuario_override and isinstance(usuario_override, dict):
        return usuario_override

    import streamlit as st
    ss = st.session_state

    raw = ss.get("usuario")
    if isinstance(raw, dict):
        return raw

    nome   = ss.get("nome", "") or ss.get("display_name", "") or str(raw or "Visitante")
    perfil = ss.get("perfil", "demo")
    email  = ss.get("email", "")
    login  = str(raw or "")

    if not (nome or email):
        return None

    return {
        "login":  login,
        "nome":   nome,
        "perfil": perfil,
        "email":  email,
    }


def _fetch_products_for_context(user_role: str) -> list[dict]:
    """
    Busca produtos ativos do banco e retorna lista de dicts
    com campos filtrados conforme o perfil do usuário.
    Retorna lista vazia silenciosamente em caso de erro.
    """
    try:
        from lib.db_utils import resolve_db_url
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker

        db_url = resolve_db_url()
        connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
        engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
        Session = sessionmaker(bind=engine)

        with Session() as session:
            rows = session.execute(
                text(
                    "SELECT sku, name, category, line, is_kit, "
                    "floor_price, suggested_retail_price "
                    "FROM products WHERE active = 1 OR active = TRUE "
                    "ORDER BY name"
                )
            ).fetchall()

        products = []
        for r in rows:
            products.append({
                "sku":                   r[0],
                "name":                  r[1],
                "category":              r[2],
                "line":                  r[3],
                "is_kit":                bool(r[4]),
                "floor_price":           float(r[5]) if r[5] is not None else 0.0,
                "suggested_retail_price": float(r[6]) if r[6] is not None else None,
            })
        return products

    except Exception:
        # Banco inacessível ou tabela ainda não criada — não quebra a IA
        return []


def stream_ia(
    pergunta: str,
    historico: list[dict] | None = None,
    usuario: dict | None = None,
    cart: dict | None = None,
    historico_pedidos: list | None = None,
):
    """
    Gerador que faz stream da resposta — use com st.write_stream().
    Injeta produtos do banco no contexto filtrado pelo role do usuário.
    """
    import streamlit as st

    _usuario           = _get_usuario_dict(usuario)
    _cart              = cart or st.session_state.get("carrinho")
    _historico_pedidos = historico_pedidos or st.session_state.get("historico_pedidos")

    # Descobre o role para filtrar visibilidade de preços
    user_role = "demo"
    if _usuario:
        user_role = _usuario.get("perfil") or _usuario.get("role") or "demo"

    # Busca produtos do banco (silencia erros — não bloqueia a IA)
    products = _fetch_products_for_context(user_role)

    context = build_context(
        usuario=_usuario,
        cart=_cart if isinstance(_cart, dict) else None,
        historico_pedidos=_historico_pedidos if isinstance(_historico_pedidos, list) else None,
        products=products,
    )

    msgs: list[dict] = []
    for m in (historico or []):
        role = m.get("role", "user") if isinstance(m, dict) else "user"
        content = m.get("content", "") if isinstance(m, dict) else ""
        if role in ("user", "assistant") and content:
            msgs.append({"role": role, "content": content})
    msgs.append({"role": "user", "content": pergunta})

    yield from chat_stream(messages=msgs, context_block=context)


def consultar_ia(
    pergunta: str,
    historico: list[dict] | None = None,
    usuario: dict | None = None,
    cart: dict | None = None,
    historico_pedidos: list | None = None,
) -> str:
    """
    Retorna a resposta completa como string (sem streaming).
    """
    return "".join(stream_ia(
        pergunta=pergunta,
        historico=historico,
        usuario=usuario,
        cart=cart,
        historico_pedidos=historico_pedidos,
    ))
