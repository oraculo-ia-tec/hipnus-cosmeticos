"""
10_IA_Consultora.py — HIPNUS COSMÉTICOS
Chat com IA (Chiara) usando Groq (llama-3.3-70b) via streaming.

Fix 2026-06-29 v7:
  - SANITIZAÇÃO do ia_msgs existente no session_state: qualquer mensagem
    com content None, "None" ou vazio é corrigida (1ª msg) ou removida.
    Resolve o "None" persistente mesmo após deploy, pois o session_state
    do Streamlit Cloud sobrevive a redeploys enquanto a sessão está ativa.
"""
from __future__ import annotations
import sys, re
from pathlib import Path

_ROOT     = Path(__file__).resolve().parents[2]
_FRONTEND = Path(__file__).resolve().parents[1]
for _p in [str(_ROOT), str(_FRONTEND)]:
    if _p not in sys.path:
        sys.path.insert(0, str(_p))

import streamlit as st
from lib import ui
from lib.auth import require_auth, build_sidebar
from lib.ia_consultora import groq_status

st.set_page_config(page_title="IA Consultora · HIPNUS", page_icon="🤖", layout="wide")
ui.inject_theme()
usuario = require_auth()
build_sidebar()

# ── CSS GLOBAL ────────────────────────────────────────────────────────
st.markdown("""
<style>
.chiara-top-avatar {
    display: flex; flex-direction: column;
    align-items: center; padding: 28px 0 20px 0; margin-bottom: 8px;
}
.chiara-top-avatar img,
.chiara-top-avatar .chiara-initial {
    width: 140px; height: 140px; border-radius: 50%; object-fit: cover;
    border: 4px solid rgba(185,131,255,0.6);
    box-shadow: 0 0 48px rgba(185,131,255,0.45), 0 0 16px rgba(236,72,153,0.25);
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 14px;
}
.chiara-top-avatar .chiara-initial {
    background: linear-gradient(135deg, #7c3aed 0%, #ec4899 100%);
    font-size: 3.5rem; font-weight: 800; color: #fff;
    flex-shrink: 0;
}
.chiara-top-name {
    font-size: 1.3rem; font-weight: 800;
    background: linear-gradient(135deg, #b983ff 0%, #ec4899 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin: 0 0 2px 0; letter-spacing: -.3px;
}
.chiara-top-title {
    font-size: .78rem; color: rgba(185,131,255,0.65);
    margin: 0; font-style: italic;
}
.chiara-status {
    display: flex; align-items: center; gap: 6px;
    margin-top: 8px; font-size: .73rem;
    color: rgba(100,220,140,0.85); font-weight: 600;
}
.chiara-status::before {
    content: ''; display: inline-block; width: 7px; height: 7px;
    border-radius: 50%; background: #64dc8c; box-shadow: 0 0 6px #64dc8c;
    animation: pulse-dot 1.8s ease-in-out infinite;
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: .5; transform: scale(.8); }
}
.chiara-divider {
    border: none; border-top: 1px solid rgba(185,131,255,0.12); margin: 0 0 8px 0;
}
</style>
""", unsafe_allow_html=True)

# ── CSS DE BOLHA ──────────────────────────────────────────────────────
_BUBBLE_CSS = """
<style>
  html, body { margin:0; padding:0; background:#0e0018 !important; }
  .hip-chat-row {
    display:flex; align-items:flex-end; gap:10px;
    margin:6px 0; max-width:820px; font-family:'Inter',sans-serif;
  }
  .hip-chat-row.user     { flex-direction:row-reverse; margin-left:auto; }
  .hip-chat-row.assistant{ flex-direction:row; }
  .hip-chat-avatar {
    width:36px; height:36px; border-radius:50%; flex-shrink:0;
    object-fit:cover; border:2px solid rgba(185,131,255,0.5);
  }
  .hip-chat-avatar-initial {
    width:36px; height:36px; border-radius:50%; flex-shrink:0;
    display:flex; align-items:center; justify-content:center;
    font-size:.95rem; font-weight:800; color:#fff;
    border:2px solid rgba(185,131,255,0.4);
  }
  .hip-chat-bubble {
    padding:11px 16px; border-radius:18px; font-size:.92rem;
    line-height:1.6; max-width:680px; word-break:break-word;
  }
  .hip-chat-row.user .hip-chat-bubble {
    background:linear-gradient(135deg,#7c3aed 0%,#5b21b6 100%);
    color:#fff !important; border-bottom-right-radius:4px;
  }
  .hip-chat-row.assistant .hip-chat-bubble {
    background:#1e1232 !important;
    border:1px solid rgba(185,131,255,0.35) !important;
    color:#e8e0ff !important;
    border-bottom-left-radius:4px;
  }
  strong { color:#d4b8ff; }
  em     { color:#c9b0f5; font-style:italic; }
</style>
"""

# ── Dados da Chiara e do usuário — fallback robusto com `or` ─────────
_chiara_b64   = st.session_state.get("chiara_foto_b64") or ""
_chiara_mime  = st.session_state.get("chiara_foto_mime") or "image/jpeg"
_chiara_nome  = st.session_state.get("chiara_nome") or "Chiara"
_chiara_cargo = (
    st.session_state.get("chiara_cargo")
    or "Terapeuta Capilar Digital · Embaixadora HIPNUS"
)
_user_b64    = st.session_state.get("avatar_b64") or ""
_user_nome   = (
    st.session_state.get("display_name")
    or st.session_state.get("nome")
    or st.session_state.get("usuario")
    or "Você"
)
_user_perfil = st.session_state.get("perfil") or "demo"
_badge_colors = {
    "super_admin": "#7c3aed", "admin": "#2563eb",
    "b2b": "#059669", "b2c": "#d97706", "demo": "#6b7280",
}
_user_color = _badge_colors.get(_user_perfil, "#7c3aed")


def _chiara_avatar_html() -> str:
    if _chiara_b64:
        src = _chiara_b64 if _chiara_b64.startswith("data:") else f"data:{_chiara_mime};base64,{_chiara_b64}"
        return f'<img class="hip-chat-avatar" src="{src}" alt="{_chiara_nome}" />'
    initial = (_chiara_nome or "C")[0].upper()
    return (
        f'<div class="hip-chat-avatar-initial" '
        f'style="background:linear-gradient(135deg,#7c3aed,#ec4899);">'
        f'{initial}</div>'
    )


def _user_avatar_html() -> str:
    if _user_b64:
        src = _user_b64 if _user_b64.startswith("data:") else f"data:image/jpeg;base64,{_user_b64}"
        return f'<img class="hip-chat-avatar" src="{src}" alt="{_user_nome}" style="border-color:{_user_color};" />'
    initial = (_user_nome or "U")[0].upper()
    return (
        f'<div class="hip-chat-avatar-initial" '
        f'style="background:linear-gradient(135deg,{_user_color},{_user_color}88);">'
        f'{initial}</div>'
    )


def _md(text: str) -> str:
    """Markdown básico → HTML seguro. re.DOTALL evita TypeError em **negrito** multilinha."""
    if not isinstance(text, str):
        text = str(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text, flags=re.DOTALL)
    text = re.sub(r'\*(.+?)\*',     r'<em>\1</em>',         text, flags=re.DOTALL)
    text = text.replace("\n", "<br>")
    return text


def _render_bubble(role: str, content: str) -> None:
    html_content = _md(content)
    if role == "user":
        avatar = _user_avatar_html()
        st.html(f"""
        {_BUBBLE_CSS}
        <div class="hip-chat-row user">
            {avatar}
            <div class="hip-chat-bubble">{html_content}</div>
        </div>
        """)
    else:
        avatar = _chiara_avatar_html()
        st.html(f"""
        {_BUBBLE_CSS}
        <div class="hip-chat-row assistant">
            {avatar}
            <div class="hip-chat-bubble">{html_content}</div>
        </div>
        """)


# ── Avatar da Chiara no topo ──────────────────────────────────────────
col_l, col_center, col_r = st.columns([1, 2, 1])
with col_center:
    initial = (_chiara_nome or "C")[0].upper()
    if _chiara_b64:
        src_topo = _chiara_b64 if _chiara_b64.startswith("data:") else f"data:{_chiara_mime};base64,{_chiara_b64}"
        st.markdown(f"""
        <div class="chiara-top-avatar">
            <img src="{src_topo}" alt="{_chiara_nome}" />
            <p class="chiara-top-name">{_chiara_nome}</p>
            <p class="chiara-top-title">{_chiara_cargo}</p>
            <div class="chiara-status">Online agora</div>
        </div>
        <hr class="chiara-divider" />
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chiara-top-avatar">
            <div class="chiara-initial">{initial}</div>
            <p class="chiara-top-name">{_chiara_nome}</p>
            <p class="chiara-top-title">{_chiara_cargo}</p>
            <div class="chiara-status">Online agora</div>
        </div>
        <hr class="chiara-divider" />
        """, unsafe_allow_html=True)

# ── Validação da IA ───────────────────────────────────────────────────
status = groq_status()
if not status["configured"]:
    st.error(
        "❌ **GROQ_API_KEY não configurada.** "
        "Acesse **Settings → Secrets** e adicione `GROQ_API_KEY`."
    )
    st.stop()

# ── Saudação inicial ──────────────────────────────────────────────────
_saudacao_padrao = (
    f"Olá! Sou a **{_chiara_nome}**, consultora virtual da Hipnus Cosméticos. 💜\n\n"
    "Posso te ajudar com:\n"
    "- Dúvidas sobre **produtos e linhas**\n"
    "- Informações sobre seu **carrinho e pedidos**\n"
    "- Como funciona o **checkout e pagamento**\n"
    "- **Convites e cadastro** de parceiros\n\n"
    "Como posso te ajudar hoje?"
)
_saudacao = st.session_state.get("chiara_saudacao") or _saudacao_padrao


def _content_invalido(v) -> bool:
    """Retorna True se o conteúdo for None, string 'None', ou vazio."""
    if v is None:
        return True
    s = str(v).strip()
    return s == "" or s.lower() == "none"


# ── Inicializa ou SANITIZA ia_msgs ────────────────────────────────────
# O session_state do Streamlit Cloud sobrevive a redeploys enquanto a
# sessão está ativa. Se ia_msgs foi inicializado com content=None em
# deploy anterior, precisamos corrigir agora antes de renderizar.
if "ia_msgs" not in st.session_state:
    st.session_state["ia_msgs"] = [{"role": "assistant", "content": _saudacao}]
else:
    msgs = st.session_state["ia_msgs"]
    sanitized = []
    for i, m in enumerate(msgs):
        if not isinstance(m, dict):
            continue
        role = m.get("role", "user")
        content = m.get("content")
        if _content_invalido(content):
            # Primeira mensagem assistant com conteúdo inválido → restaura saudação
            if i == 0 and role == "assistant":
                sanitized.append({"role": "assistant", "content": _saudacao})
            # Qualquer outra mensagem inválida é descartada
        else:
            sanitized.append({"role": role, "content": str(content)})
    # Garante sempre pelo menos a saudação
    if not sanitized:
        sanitized = [{"role": "assistant", "content": _saudacao}]
    st.session_state["ia_msgs"] = sanitized

# ── Histórico ─────────────────────────────────────────────────────────
for msg in st.session_state["ia_msgs"]:
    _render_bubble(msg["role"], msg["content"])

# ── Input + streaming ─────────────────────────────────────────────────
if prompt := st.chat_input(f"Pergunte à {_chiara_nome} sobre produtos, pedidos, pagamentos..."):
    st.session_state["ia_msgs"].append({"role": "user", "content": prompt})
    _render_bubble("user", prompt)

    avatar_html = _chiara_avatar_html()
    streaming_placeholder = st.empty()
    resposta_chunks: list[str] = []

    try:
        from lib.ia_client import stream_ia
        for chunk in stream_ia(
            pergunta=prompt,
            historico=st.session_state["ia_msgs"][:-1],
        ):
            resposta_chunks.append(chunk)
            parcial = _md("".join(resposta_chunks))
            streaming_placeholder.html(f"""
            {_BUBBLE_CSS}
            <div class="hip-chat-row assistant">
                {avatar_html}
                <div class="hip-chat-bubble">{parcial}<span style="opacity:.5;color:#b983ff;">|</span></div>
            </div>
            """)
        resposta = "".join(resposta_chunks)
        streaming_placeholder.html(f"""
        {_BUBBLE_CSS}
        <div class="hip-chat-row assistant">
            {avatar_html}
            <div class="hip-chat-bubble">{_md(resposta)}</div>
        </div>
        """)
    except RuntimeError as e:
        msg_erro = str(e)
        if "GROQ_API_KEY" in msg_erro:
            resposta = "❌ Chave da IA não configurada. Adicione GROQ_API_KEY nos Secrets."
        elif "openai" in msg_erro.lower():
            resposta = "❌ Pacote openai não instalado. Adicione ao requirements.txt."
        else:
            resposta = f"⚠️ Erro: {msg_erro}"
        streaming_placeholder.html(f"""
        {_BUBBLE_CSS}
        <div class="hip-chat-row assistant">
            {avatar_html}
            <div class="hip-chat-bubble">{resposta}</div>
        </div>
        """)
    except Exception as e:
        resposta = f"⚠️ Erro inesperado: {e}"
        streaming_placeholder.html(f"""
        {_BUBBLE_CSS}
        <div class="hip-chat-row assistant">
            {avatar_html}
            <div class="hip-chat-bubble">{resposta}</div>
        </div>
        """)

    st.session_state["ia_msgs"].append({"role": "assistant", "content": resposta or ""})

# ── Botão limpar ──────────────────────────────────────────────────────
if len(st.session_state["ia_msgs"]) > 1:
    if st.button("🗑️ Limpar conversa", key="clear_chat"):
        st.session_state["ia_msgs"] = [{"role": "assistant", "content": _saudacao}]
        st.rerun()
