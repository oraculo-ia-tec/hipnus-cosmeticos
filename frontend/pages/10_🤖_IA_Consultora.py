"""
10_🤖_IA_Consultora.py — HIPNUS COSMÉTICOS
===========================================
Skill: IA Consultora
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT     = Path(__file__).resolve().parents[2]
_FRONTEND = Path(__file__).resolve().parents[1]
for _p in [str(_ROOT), str(_FRONTEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
from lib import ui, components
from lib.auth import require_auth, sidebar_logo, sidebar_user_info, sidebar_logout_button
from lib.ia_consultora import build_context, chat_stream, groq_status

st.set_page_config(
    page_title="IA Consultora · HIPNUS",
    page_icon="🤖",
    layout="centered",
)
ui.inject_theme()

usuario = require_auth()
sidebar_logo()
sidebar_user_info()
sidebar_logout_button()

components.page_header(
    title="IA Consultora",
    subtitle="Pergunte sobre produtos, pedidos, pagamentos e muito mais.",
)

# ─── Avatar do usuário para o chat ──────────────────────────────────────────
perfil     = st.session_state.get("perfil", "b2c")
avatar_b64 = st.session_state.get("avatar_b64", None)

_icones_perfil = {"super_admin": "⭐", "admin": "🛡️", "b2b": "🎤", "b2c": "👤", "demo": "👀"}
USER_AVATAR = avatar_b64 if avatar_b64 else _icones_perfil.get(perfil, "👤")

# ─── Verifica configuração GROQ ──────────────────────────────────────────
status = groq_status()

if not status["configured"]:
    st.error(
        "❌ A IA Consultora não está disponível no momento. "
        "Entre em contato com o suporte."
    )
    st.stop()

# ─── Contexto da sessão ─────────────────────────────────────────────────
cart              = st.session_state.get("cart", {})
historico_pedidos = st.session_state.get("historico_pedidos", [])

usuario_ctx = {
    "nome":   st.session_state.get("nome") or st.session_state.get("display_name", ""),
    "perfil": perfil,
    "email":  st.session_state.get("email", ""),
}

context_block = build_context(
    usuario=usuario_ctx,
    cart=cart,
    historico_pedidos=historico_pedidos,
    smtp_ok=True,
)

# ─── Histórico de chat na sessão ─────────────────────────────────────────────
if "_ia_messages" not in st.session_state:
    st.session_state["_ia_messages"] = []

messages: list[dict] = st.session_state["_ia_messages"]

# ─── Sidebar: limpar conversa ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🤖 IA Consultora")
    st.divider()
    if st.button("🗑️ Limpar conversa", use_container_width=True):
        st.session_state["_ia_messages"] = []
        st.rerun()

# ─── Prompts rápidos ──────────────────────────────────────────────────
PROMPTS_RAPIDOS = [
    ("🛒 O que tem no meu carrinho?",         "O que tem no meu carrinho?"),
    ("💳 Quais pedidos fiz nesta sessão?",     "Quais pedidos fiz nesta sessão?"),
    ("🤝 Como funciona o split com parceiros?", "Como funciona o split entre Hipnus e parceiros?"),
    ("💰 Como calcular meu repasse?",           "Como calculo o valor do meu repasse como parceiro?"),
    ("💆 Quais produtos indicar para cabelos danificados?", "Quais produtos Hipnus indicar para cabelos danificados?"),
    ("📦 Como faço um pedido?",                "Como faço um pedido na loja Hipnus?"),
]

if not messages:
    st.markdown("**Atalhos rápidos:**")
    cols = st.columns(3)
    for i, (label, prompt) in enumerate(PROMPTS_RAPIDOS):
        with cols[i % 3]:
            if st.button(label, use_container_width=True, key=f"_qp_{i}"):
                st.session_state["_ia_messages"].append({"role": "user", "content": prompt})
                st.rerun()

# ─── Renderiza histórico ─────────────────────────────────────────────────
for msg in messages:
    av = "🤖" if msg["role"] == "assistant" else USER_AVATAR
    with st.chat_message(msg["role"], avatar=av):
        st.markdown(msg["content"])

# ─── Input do usuário ──────────────────────────────────────────────────
if prompt_input := st.chat_input("Pergunte sobre produtos, pedidos, pagamentos..."):
    messages.append({"role": "user", "content": prompt_input})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt_input)

    with st.chat_message("assistant", avatar="🤖"):
        try:
            resposta_placeholder = st.empty()
            full_text = ""
            for chunk in chat_stream(
                messages[:-1] + [{"role": "user", "content": prompt_input}],
                context_block,
            ):
                full_text += chunk
                resposta_placeholder.markdown(full_text + "▮")
            resposta_placeholder.markdown(full_text)
            messages.append({"role": "assistant", "content": full_text})
        except RuntimeError as exc:
            st.error(str(exc))

    st.session_state["_ia_messages"] = messages
