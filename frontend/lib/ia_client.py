"""
ia_client.py — HIPNUS COSMÉTICOS
====================================
Adaptador entre a página 10_IA_Consultora e o motor ia_consultora.py.
Expõe consultar_ia() (resposta completa) e stream_ia() (gerador).
"""
from __future__ import annotations
import sys
from pathlib import Path

_ROOT     = Path(__file__).resolve().parents[2]
_FRONTEND = Path(__file__).resolve().parents[1]
for _p in [str(_ROOT), str(_FRONTEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from lib.ia_consultora import chat_stream, build_context, groq_status  # noqa: E402


def consultar_ia(
    pergunta: str,
    historico: list[dict] | None = None,
    usuario: dict | None = None,
    cart: dict | None = None,
    historico_pedidos: list | None = None,
) -> str:
    """
    Envia pergunta + histórico para a Groq e retorna a resposta completa como string.
    Levanta RuntimeError com mensagem amigável se a chave não estiver configurada.
    """
    import streamlit as st

    # Monta contexto dinâmico da sessão
    _usuario          = usuario or st.session_state.get("usuario")
    _cart             = cart    or st.session_state.get("carrinho")
    _historico_pedidos = historico_pedidos or st.session_state.get("historico_pedidos")

    context = build_context(
        usuario=_usuario,
        cart=_cart if isinstance(_cart, dict) else None,
        historico_pedidos=_historico_pedidos,
    )

    # Monta lista de mensagens no formato OpenAI
    msgs: list[dict] = []
    for m in (historico or []):
        role = m.get("role", "user")
        if role in ("user", "assistant"):
            msgs.append({"role": role, "content": m.get("content", "")})
    msgs.append({"role": "user", "content": pergunta})

    # Acumula stream em string
    partes: list[str] = []
    for chunk in chat_stream(messages=msgs, context_block=context):
        partes.append(chunk)
    return "".join(partes)


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

    _usuario           = usuario or st.session_state.get("usuario")
    _cart              = cart    or st.session_state.get("carrinho")
    _historico_pedidos = historico_pedidos or st.session_state.get("historico_pedidos")

    context = build_context(
        usuario=_usuario,
        cart=_cart if isinstance(_cart, dict) else None,
        historico_pedidos=_historico_pedidos,
    )

    msgs: list[dict] = []
    for m in (historico or []):
        role = m.get("role", "user")
        if role in ("user", "assistant"):
            msgs.append({"role": role, "content": m.get("content", "")})
    msgs.append({"role": "user", "content": pergunta})

    yield from chat_stream(messages=msgs, context_block=context)
