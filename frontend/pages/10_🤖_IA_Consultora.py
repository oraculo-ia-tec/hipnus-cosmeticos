"""
10_IA_Consultora.py — HIPNUS COSMÉTICOS
Chat com IA usando Groq (llama-3.3-70b) via streaming.
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
from lib.auth import require_auth, build_sidebar
from lib.ia_consultora import groq_status

st.set_page_config(page_title="IA Consultora · HIPNUS", page_icon="🤖", layout="wide")
ui.inject_theme()
usuario = require_auth()
build_sidebar()

components.page_header(
    title="IA Consultora",
    subtitle="Tire dúvidas sobre produtos, linhas, pedidos e pagamentos com nossa IA especializada.",
    kicker="🤖 Assistente Hipnus",
)

# ── Status da IA ──────────────────────────────────────────────────────────────
status = groq_status()
if not status["configured"]:
    st.error(
        "❌ **GROQ_API_KEY não configurada.** "
        "Acesse o painel do Streamlit Cloud → **Settings → Secrets** e adicione:\n\n"
        "```toml\nGROQ_API_KEY = \"gsk_seu_token_aqui\"\n```\n\n"
        "💡 Crie sua chave grátis em [console.groq.com](https://console.groq.com)"
    )
    st.stop()
else:
    st.caption(f"🟢 IA ativa · Modelo: `{status['model']}`")

# ── Histórico do chat ──────────────────────────────────────────────────────────
if "ia_msgs" not in st.session_state:
    st.session_state["ia_msgs"] = [
        {
            "role": "assistant",
            "content": "Olá! Sou a consultora virtual da Hipnus Cosméticos. 💜\n\nPosso te ajudar com:\n- Dúvidas sobre **produtos e linhas**\n- Informações sobre seu **carrinho e pedidos**\n- Como funciona o **checkout e pagamento**\n- **Convites e cadastro** de parceiros\n\nComo posso te ajudar hoje?",
        }
    ]

# Renderiza mensagens anteriores
for msg in st.session_state["ia_msgs"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Input e resposta streaming ────────────────────────────────────────────────────
if prompt := st.chat_input("Pergunte sobre produtos, pedidos, pagamentos..."):
    # Adiciona mensagem do usuário
    st.session_state["ia_msgs"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gera resposta com streaming
    with st.chat_message("assistant"):
        try:
            from lib.ia_client import stream_ia
            resposta = st.write_stream(
                stream_ia(
                    pergunta=prompt,
                    historico=st.session_state["ia_msgs"][:-1],
                )
            )
        except RuntimeError as e:
            msg_erro = str(e)
            if "GROQ_API_KEY" in msg_erro:
                resposta = (
                    "❌ **Chave da IA não configurada.**\n\n"
                    "Adicione `GROQ_API_KEY` nos **Secrets** do Streamlit Cloud.\n"
                    "💡 Acesse: console.groq.com para criar sua chave grátis."
                )
            elif "openai" in msg_erro.lower():
                resposta = (
                    "❌ **Pacote `openai` não instalado.**\n\n"
                    "Adicione `openai` ao `requirements.txt` e reinicie o app."
                )
            else:
                resposta = f"⚠️ Erro na IA: {msg_erro}"
            st.markdown(resposta)
        except Exception as e:
            resposta = f"⚠️ Erro inesperado: {e}"
            st.markdown(resposta)

    st.session_state["ia_msgs"].append({"role": "assistant", "content": resposta or ""})

# ── Botão limpar chat ────────────────────────────────────────────────────────────
if len(st.session_state["ia_msgs"]) > 1:
    if st.button("🗑️ Limpar conversa", key="clear_chat"):
        st.session_state["ia_msgs"] = [
            {
                "role": "assistant",
                "content": "Conversa reiniciada! Como posso te ajudar? 💜",
            }
        ]
        st.rerun()
