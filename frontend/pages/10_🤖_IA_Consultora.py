"""
10_IA_Consultora.py — HIPNUS COSMÉTICOS
Chat com IA (Chiara) usando Groq (llama-3.3-70b) via streaming.
Avatares: foto da Chiara no topo + avatar redondo nas mensagens do assistente.
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

# ── CSS do chat ───────────────────────────────────────────────────────────────
st.html("""
<style>
/* Avatar da Chiara no topo */
.chiara-top-avatar {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 28px 0 20px 0;
    margin-bottom: 8px;
}
.chiara-top-avatar img,
.chiara-top-avatar .chiara-initial {
    width: 140px;
    height: 140px;
    border-radius: 50%;
    object-fit: cover;
    border: 4px solid rgba(185,131,255,0.6);
    box-shadow: 0 0 48px rgba(185,131,255,0.45), 0 0 16px rgba(236,72,153,0.25);
    display: block;
    margin-bottom: 14px;
}
.chiara-top-avatar .chiara-initial {
    background: linear-gradient(135deg, #7c3aed 0%, #ec4899 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 3.5rem;
    font-weight: 800;
    color: #fff;
}
.chiara-top-name {
    font-size: 1.3rem;
    font-weight: 800;
    background: linear-gradient(135deg, #b983ff 0%, #ec4899 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 2px 0;
    letter-spacing: -.3px;
}
.chiara-top-title {
    font-size: .78rem;
    color: rgba(185,131,255,0.65);
    margin: 0;
    font-style: italic;
}
.chiara-status {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 8px;
    font-size: .73rem;
    color: rgba(100,220,140,0.85);
    font-weight: 600;
}
.chiara-status::before {
    content: '';
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #64dc8c;
    box-shadow: 0 0 6px #64dc8c;
    animation: pulse-dot 1.8s ease-in-out infinite;
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: .5; transform: scale(.8); }
}
.chiara-divider {
    border: none;
    border-top: 1px solid rgba(185,131,255,0.12);
    margin: 0 0 8px 0;
}
</style>
""")

# ── Avatar da Chiara no topo (centralizado) ──────────────────────────────────
_chiara_b64  = st.session_state.get("chiara_foto_b64", "")
_chiara_mime = st.session_state.get("chiara_foto_mime", "image/jpeg")
_chiara_nome = st.session_state.get("chiara_nome", "Chiara")
_chiara_cargo = st.session_state.get(
    "chiara_cargo",
    "Terapeuta Capilar Digital · Embaixadora HIPNUS"
)

# Centraliza via colunas
col_l, col_center, col_r = st.columns([1, 2, 1])
with col_center:
    if _chiara_b64:
        st.html(f"""
        <div class="chiara-top-avatar">
            <img src="data:{_chiara_mime};base64,{_chiara_b64}"
                 alt="{_chiara_nome}" />
            <p class="chiara-top-name">{_chiara_nome}</p>
            <p class="chiara-top-title">{_chiara_cargo}</p>
            <div class="chiara-status">Online agora</div>
        </div>
        <hr class="chiara-divider" />
        """)
    else:
        # Placeholder com inicial luminosa se ainda sem foto
        initial = _chiara_nome[0].upper() if _chiara_nome else "C"
        st.html(f"""
        <div class="chiara-top-avatar">
            <div class="chiara-initial">{initial}</div>
            <p class="chiara-top-name">{_chiara_nome}</p>
            <p class="chiara-top-title">{_chiara_cargo}</p>
            <div class="chiara-status">Online agora</div>
        </div>
        <hr class="chiara-divider" />
        """)

# ── Validação silenciosa da IA (sem exibir info técnica) ─────────────────────
status = groq_status()
if not status["configured"]:
    st.error(
        "❌ **GROQ_API_KEY não configurada.** "
        "Acesse o painel do Streamlit Cloud → **Settings → Secrets** e adicione:\n\n"
        "```toml\nGROQ_API_KEY = \"gsk_seu_token_aqui\"\n```\n\n"
        "💡 Crie sua chave grátis em [console.groq.com](https://console.groq.com)"
    )
    st.stop()

# ── Saudação inicial personalizada ───────────────────────────────────────────
_saudacao_padrao = (
    f"Olá! Sou a **{_chiara_nome}**, consultora virtual da Hipnus Cosméticos. 💜\n\n"
    "Posso te ajudar com:\n"
    "- Dúvidas sobre **produtos e linhas**\n"
    "- Informações sobre seu **carrinho e pedidos**\n"
    "- Como funciona o **checkout e pagamento**\n"
    "- **Convites e cadastro** de parceiros\n\n"
    "Como posso te ajudar hoje?"
)
_saudacao = st.session_state.get("chiara_saudacao", _saudacao_padrao)

# ── Histórico do chat ──────────────────────────────────────────────────────────
if "ia_msgs" not in st.session_state:
    st.session_state["ia_msgs"] = [{"role": "assistant", "content": _saudacao}]

# Renderiza mensagens anteriores
for msg in st.session_state["ia_msgs"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Input e resposta streaming ─────────────────────────────────────────────────
if prompt := st.chat_input(f"Pergunte à {_chiara_nome} sobre produtos, pedidos, pagamentos..."):
    st.session_state["ia_msgs"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

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
                    "Adicione `GROQ_API_KEY` nos **Secrets** do Streamlit Cloud."
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

# ── Botão limpar chat ──────────────────────────────────────────────────────────
if len(st.session_state["ia_msgs"]) > 1:
    if st.button("🗑️ Limpar conversa", key="clear_chat"):
        st.session_state["ia_msgs"] = [{"role": "assistant", "content": _saudacao}]
        st.rerun()
