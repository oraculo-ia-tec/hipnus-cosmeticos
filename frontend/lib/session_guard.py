"""
session_guard.py — HIPNUS COSMÉTICOS
========================================
Skill: 🔐 JWT Auto-Refresh

Responsabilidades:
  1. Registrar o timestamp de login em st.session_state["session_start"]
  2. Calcular o tempo restante da sessão (padrão: 8 h)
  3. Exibir um st.dialog de aviso nos últimos 15 minutos
  4. Oferecer botão "Renovar Sessão" que reseta o timestamp sem logout
  5. Forçar logout silencioso se o tempo expirar sem renovação

Uso — chame check_session_expiry() no topo de CADA página autenticada:

    from lib.session_guard import check_session_expiry
    check_session_expiry()
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta

import streamlit as st

# ─── Configuração ───────────────────────────────────────────────────────────
SESSION_DURATION_H: int = 8          # duração total da sessão em horas
WARN_BEFORE_MIN: int    = 15         # minutos antes do fim para exibir aviso
_LOGIN_PAGE             = "streamlit_app.py"


# ─── Helpers internos ───────────────────────────────────────────────────────

def _get_remaining() -> tuple[int, int]:
    """Retorna (minutos_restantes, segundos_restantes) da sessão atual."""
    start: float = st.session_state.get("session_start", time.time())
    elapsed = time.time() - start
    total   = SESSION_DURATION_H * 3600
    remaining = max(0.0, total - elapsed)
    mins = int(remaining // 60)
    secs = int(remaining % 60)
    return mins, secs


def _renovar_sessao() -> None:
    """Reseta o timestamp de início sem encerrar a sessão."""
    st.session_state["session_start"] = time.time()
    st.session_state["_jwt_dialog_shown"] = False
    st.rerun()


def _forcar_logout() -> None:
    """Limpa a sessão e redireciona para login."""
    keys_to_clear = [
        "autenticado", "usuario", "perfil", "nome",
        "display_name", "email", "token", "via_api",
        "avatar_b64", "session_start", "_jwt_dialog_shown",
    ]
    for k in keys_to_clear:
        st.session_state.pop(k, None)
    st.query_params.clear()
    st.switch_page(_LOGIN_PAGE)


# ─── Dialog de aviso ────────────────────────────────────────────────────────

@st.dialog("⏳ Sua sessão está prestes a expirar", width="small")
def _dialog_aviso_sessao(mins: int, secs: int) -> None:
    """
    st.dialog nativo do Streamlit — bloqueia a UI e exige ação do usuário.
    Exibido automaticamente nos últimos WARN_BEFORE_MIN minutos.
    """
    st.html(
        f"""
        <div style="text-align:center; padding: 8px 0 4px;">
            <div style="
                font-size: 3rem; line-height: 1;
                margin-bottom: 12px;
            ">🔐</div>
            <p style="
                font-size: 1rem; font-weight: 700;
                color: #1a1430; margin: 0 0 6px;
            ">Sessão expira em:</p>
            <div style="
                display: inline-block;
                background: #fef2f2;
                border: 1.5px solid #fca5a5;
                border-radius: 12px;
                padding: 10px 28px;
                font-size: 2rem;
                font-weight: 800;
                color: #dc2626;
                letter-spacing: 2px;
                font-variant-numeric: tabular-nums;
            ">{mins:02d}:{secs:02d}</div>
            <p style="
                font-size: 0.82rem; color: #6b7280;
                margin: 14px 0 0;
                line-height: 1.5;
            ">
                Clique em <strong>Renovar Sessão</strong> para continuar
                trabalhando por mais {SESSION_DURATION_H}h sem precisar
                fazer login novamente.
            </p>
        </div>
        """
    )

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button(
            "🔄 Renovar Sessão",
            type="primary",
            use_container_width=True,
            key="_jwt_btn_renovar",
        ):
            _renovar_sessao()

    with col_b:
        if st.button(
            "🚶 Sair agora",
            use_container_width=True,
            key="_jwt_btn_sair",
        ):
            _forcar_logout()


@st.dialog("🔒 Sessão encerrada", width="small")
def _dialog_sessao_expirada() -> None:
    """
    st.dialog exibido quando o tempo expirou antes de o usuário renovar.
    """
    st.html(
        """
        <div style="text-align:center; padding: 8px 0 12px;">
            <div style="font-size: 3rem; margin-bottom: 12px;">⌛</div>
            <p style="font-size: 1rem; font-weight: 700; color: #1a1430; margin: 0 0 8px;">
                Sua sessão expirou por inatividade.
            </p>
            <p style="font-size: 0.85rem; color: #6b7280; line-height: 1.55; margin: 0;">
                Por segurança, sua sessão de {SESSION_DURATION_H}h foi encerrada
                automaticamente. Faça login novamente para continuar.
            </p>
        </div>
        """
    )
    if st.button(
        "Ir para o Login  →",
        type="primary",
        use_container_width=True,
        key="_jwt_btn_ir_login",
    ):
        _forcar_logout()


# ─── API pública ─────────────────────────────────────────────────────────────

def iniciar_sessao() -> None:
    """
    Deve ser chamado UMA VEZ ao gravar a sessão após login bem-sucedido.
    Registra o timestamp de início e reseta flags de controle.
    """
    if "session_start" not in st.session_state:
        st.session_state["session_start"] = time.time()
    st.session_state.setdefault("_jwt_dialog_shown", False)


def check_session_expiry() -> None:
    """
    Deve ser chamado no topo de CADA página autenticada.

    Fluxo:
      - Se não há session_start → inicializa (compatibilidade com sessões anteriores)
      - Se expirou → exibe dialog de expiração e para o script
      - Se nos últimos WARN_BEFORE_MIN minutos → exibe dialog de aviso UMA vez
      - Caso contrário → nada acontece, fluxo normal da página
    """
    if not st.session_state.get("autenticado"):
        return  # não autenticado — require_auth já trata o redirect

    # Compatibilidade retroativa: sessões sem session_start recebem
    # um timestamp "confortável" de agora (não expira imediatamente)
    if "session_start" not in st.session_state:
        st.session_state["session_start"] = time.time()
        st.session_state["_jwt_dialog_shown"] = False

    mins, secs = _get_remaining()

    # ── Sessão expirada ──────────────────────────────────────────────
    if mins == 0 and secs == 0:
        _dialog_sessao_expirada()
        st.stop()

    # ── Janela de aviso ──────────────────────────────────────────────
    if mins < WARN_BEFORE_MIN and not st.session_state.get("_jwt_dialog_shown"):
        st.session_state["_jwt_dialog_shown"] = True
        _dialog_aviso_sessao(mins, secs)
        st.stop()
