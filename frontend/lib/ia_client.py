"""
ia_client.py — HIPNUS COSMÉTICOS
====================================
Adaptador entre a página IA Consultora e o motor ia_consultora.py.
Expõe stream_ia() (gerador para st.write_stream) e consultar_ia() (string completa).
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

    # Se por acaso já for dict, usa direto
    raw = ss.get("usuario")
    if isinstance(raw, dict):
        return raw

    # Monta dict a partir dos campos individuais do session_state
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


def stream_ia(
    pergunta: str,
    historico: list[dict] | None = None,
    usuario: dict | None = None,
    cart: dict | None = None,
    historico_pedidos: list | None = None,
):
    """
    Gerador que faz stream da resposta — use com st.write_stream().
    """
    import streamlit as st

    _usuario           = _get_usuario_dict(usuario)
    _cart              = cart or st.session_state.get("carrinho")
    _historico_pedidos = historico_pedidos or st.session_state.get("historico_pedidos")

    context = build_context(
        usuario=_usuario,
        cart=_cart if isinstance(_cart, dict) else None,
        historico_pedidos=_historico_pedidos if isinstance(_historico_pedidos, list) else None,
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
