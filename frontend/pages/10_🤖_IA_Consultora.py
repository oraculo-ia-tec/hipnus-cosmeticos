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
from lib.email_service import smtp_status

st.set_page_config(
    page_title="IA Consultora · HIPNUS",
    page_icon="🤖",
    layout="centered",
)
ui.inject_theme()

usuario = require_auth()
sidebar_logo()
sidebar_user_info()
ui.sidebar_cart_summary()
sidebar_logout_button()

components.page_header(
    title="IA Consultora",
    subtitle="Pergunte sobre pedidos, split, pagamentos, convites e muito mais.",
    kicker="🤖 Powered by Groq · Llama 3.3 70B",
)

# ─── Avatar do usuário para o chat ──────────────────────────────────────────
perfil       = st.session_state.get("perfil", "b2c")
avatar_b64   = st.session_state.get("avatar_b64", None)

# Fallback por perfil quando não há foto
_icones_perfil = {"super_admin": "⭐", "admin": "🛡️", "b2b": "🎤", "b2c": "👤", "demo": "👀"}
USER_AVATAR = avatar_b64 if avatar_b64 else _icones_perfil.get(perfil, "👤")

# ─── Verifica configuração GROQ ──────────────────────────────────────────
status = groq_status()

if not status["configured"]:
    st.error(
        "❌ **GROQ\_API\_KEY não encontrada.**\n\n"
        "Adicione nos **Secrets do Streamlit Cloud**:\n"
        "```toml\n[groq]\nGROQ_API_KEY = \"gsk_...\"\ n```"
    )
    st.stop()

# ─── Contexto da sessão ─────────────────────────────────────────────────
cart              = st.session_state.get("cart", {})
historico_pedidos = st.session_state.get("historico_pedidos", [])
smtp_ok           = smtp_status().get("ready", False)

usuario_ctx = {
    "nome":   st.session_state.get("nome")   or st.session_state.get("display_name", ""),
    "perfil": perfil,
    "email":  st.session_state.get("email", ""),
}

context_block = build_context(
    usuario=usuario_ctx,
    cart=cart,
    historico_pedidos=historico_pedidos,
    smtp_ok=smtp_ok,
)

# ─── Histórico de chat na sessão ─────────────────────────────────────────────
if "_ia_messages" not in st.session_state:
    st.session_state["_ia_messages"] = []

messages: list[dict] = st.session_state["_ia_messages"]

# ─── Sidebar: info + limpar ───────────────────────────────────────────────
smtp_label = "✅ ativo" if smtp_ok else "⚠️ inativo"
with st.sidebar:
    st.markdown("### 🤖 IA Consultora")
    st.caption(f"Modelo: `{status['model']}`")
    st.caption(f"Itens no carrinho: **{len(cart)}**")
    st.caption(f"Pedidos na sessão: **{len(historico_pedidos)}**")
    st.caption(f"SMTP: {smtp_label}")
    st.divider()
    if st.button("🗑️ Limpar conversa", use_container_width=True):
        st.session_state["_ia_messages"] = []
        st.rerun()

# ─── Prompts rápidos ──────────────────────────────────────────────────
PROMPTS_RAPIDOS = [
    ("🛒 O que tem no meu carrinho?",          "O que tem no meu carrinho?"),
    ("💳 Quais pedidos fiz nesta sessão?",      "Quais pedidos fiz nesta sessão?"),
    ("🤝 Como funciona o split com parceiros?",  "Como funciona o split entre Hipnus e parceiros?"),
    ("💰 Como calcular meu repasse?",            "Como calculo o valor do meu repasse como parceiro?"),
    ("📧 O e-mail está configurado?",           "O e-mail transacional está configurado e funcionando?"),
    ("📃 Como funciona o PIX no checkout?",      "Como funciona o pagamento via PIX no checkout?"),
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
if prompt_input := st.chat_input("Pergunte sobre pedidos, split, pagamentos..."):
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
