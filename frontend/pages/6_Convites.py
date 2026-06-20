"""
6_Convites.py — HIPNUS COSMÉTICOS
====================================
Gerenciamento de convites de cadastro para parceiros e distribuidores.

Modos de operação:
  1. Online  — usa o endpoint POST /api/v1/invites/ da API FastAPI;
               persiste no banco, envia e-mail via SMTP Hostinger.
  2. Offline — gera token UUID localmente, monta link de cadastro e
               exibe para cópia manual; histórico em st.session_state.
               Funciona no Streamlit Cloud sem backend deployado.

Fluxo:
  - Admin preenche e-mail + perfil e clica em "Gerar convite"
  - Se API disponível: cria convite real, envia e-mail, exibe link
  - Se API offline:    gera token local, exibe link copiável
  - Histórico da sessão exibe todos os convites gerados na sessão atual
"""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
import streamlit as st
from lib import ui
from lib.auth import require_auth, sidebar_logo, sidebar_user_info, sidebar_logout_button
from lib import components
from lib.config import API_V1, APP_URL

# ─── Setup ───────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Convites · HIPNUS", page_icon="📨", layout="wide")
ui.inject_theme()
usuario = require_auth(perfis_permitidos=["super_admin", "admin"])
sidebar_logo()
sidebar_user_info()
sidebar_logout_button()

# Histórico local de convites gerados na sessão
if "_convites_gerados" not in st.session_state:
    st.session_state["_convites_gerados"] = []


# ─── Helpers ─────────────────────────────────────────────────────────────────
def _gerar_convite_offline(email: str, role: str, criado_por: str) -> dict:
    """
    Gera convite localmente sem depender da API.
    Token UUID4 hex, link de cadastro montado com APP_URL.
    """
    token      = uuid.uuid4().hex
    signup_url = f"{APP_URL}/Cadastro_Parceiro?invite={token}"
    expires_at = datetime.utcnow() + timedelta(days=7)
    return {
        "token":      token,
        "email":      email,
        "role":       role,
        "created_by": criado_por,
        "signup_url": signup_url,
        "expires_at": expires_at.strftime("%d/%m/%Y %H:%M") + " UTC",
        "email_sent": False,
        "origem":     "offline",
    }


def _gerar_convite_api(email: str, role: str, token_jwt: str | None) -> dict | None:
    """
    Tenta criar convite via API. Retorna dict com dados ou None se falhar.
    """
    headers = {"Authorization": f"Bearer {token_jwt}"} if token_jwt else {}
    try:
        r = httpx.post(
            f"{API_V1}/invites/",
            json={"email": email, "role": role},
            headers=headers,
            timeout=6.0,
        )
        if r.status_code == 201:
            data = r.json()
            data["origem"] = "api"
            data["expires_at"] = data.get("expires_at", "")
            return data
        return None
    except Exception:
        return None


def _badge_role(role: str) -> str:
    return {"b2b": "🎤 Profissional", "b2c": "👤 Cliente", "admin": "🛡️ Admin"}.get(role, role)


def _badge_origem(origem: str) -> str:
    return "🟢 API" if origem == "api" else "🟡 Offline"


# ─── Header ──────────────────────────────────────────────────────────────────
components.page_header(
    title="Convites de Parceiros",
    subtitle="Gere e gerencie convites personalizados para novos distribuidores, salões e parceiros.",
    kicker="Área Admin",
)

# ─── Formulário de geração ───────────────────────────────────────────────────
components.section_title("Gerar novo convite")

with st.form("form_invite", clear_on_submit=True):
    col1, col2 = st.columns([3, 1])
    with col1:
        email_dest = st.text_input(
            "E-mail do destinatário",
            placeholder="parceiro@email.com",
        )
    with col2:
        role_dest = st.selectbox(
            "Perfil do convidado",
            ["b2b", "admin", "b2c"],
            format_func=lambda r: {"b2b": "Profissional / Salão", "b2c": "Cliente Final", "admin": "Administrador"}.get(r, r),
        )
    submitted = st.form_submit_button("📨 Gerar convite", use_container_width=True, type="primary")

if submitted:
    if not email_dest or "@" not in email_dest:
        st.error("⚠️ Informe um e-mail válido para o destinatário.")
    else:
        criado_por = usuario.get("login", "admin")
        token_jwt  = st.session_state.get("token")

        with st.spinner("Gerando convite..."):
            # Tenta via API primeiro
            resultado = _gerar_convite_api(email_dest, role_dest, token_jwt)

            if resultado is None:
                # Fallback offline
                resultado = _gerar_convite_offline(email_dest, role_dest, criado_por)

        # Salva no histórico da sessão
        st.session_state["_convites_gerados"].insert(0, resultado)

        # ─── Feedback visual ─────────────────────────────────────────────
        signup_url = resultado.get("signup_url", "")
        email_sent = resultado.get("email_sent", False)
        origem     = resultado.get("origem", "offline")

        if origem == "api" and email_sent:
            st.success(f"✅ Convite enviado por e-mail para **{email_dest}**!")
        elif origem == "api" and not email_sent:
            st.warning("✅ Convite criado na API, mas o **e-mail não foi enviado** (verifique as configurações SMTP).")
        else:
            st.info("📋 API offline — convite gerado localmente. Copie o link abaixo e envie manualmente.")

        # Card com link copiável
        st.html(f"""
        <div style="background:#f3f0ff;border:1.5px solid #c4b5fd;border-radius:12px;
                    padding:18px 20px;margin:12px 0;">
            <div style="font-size:.72rem;font-weight:700;letter-spacing:.8px;
                        text-transform:uppercase;color:#7C3AED;margin-bottom:6px;">
                🔗 Link de cadastro — expira em 7 dias
            </div>
            <div style="font-size:.88rem;color:#1A1430;word-break:break-all;
                        background:#fff;padding:10px 14px;border-radius:8px;
                        border:1px solid #ddd5f8;font-family:monospace;">
                {signup_url}
            </div>
            <div style="font-size:.75rem;color:#6B6580;margin-top:8px;">
                Perfil: <strong>{_badge_role(role_dest)}</strong> &nbsp;·&nbsp;
                Criado por: <strong>{criado_por}</strong> &nbsp;·&nbsp;
                Origem: {_badge_origem(origem)}
            </div>
        </div>
        """)

        # Área de texto para copiar facilmente
        st.text_area(
            "Copie o link de cadastro:",
            value=signup_url,
            height=80,
            help="Selecione o texto acima e copie (Ctrl+C / Cmd+C)",
        )

        if origem == "offline":
            st.html("""
            <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:10px;
                        padding:12px 16px;font-size:.82rem;color:#92400e;margin-top:4px;">
                <strong>⚙️ Para ativar envio automático de e-mail:</strong><br>
                Configure <code>HIPNUS_API_URL</code> nos Streamlit Secrets apontando para
                sua VPS Hostinger onde o backend FastAPI está rodando.
            </div>
            """)

# ─── Histórico da sessão ─────────────────────────────────────────────────────
components.divider()
components.section_title("Convites gerados nesta sessão")

convites_sessao = st.session_state.get("_convites_gerados", [])

if not convites_sessao:
    # Tenta buscar da API também
    token_jwt = st.session_state.get("token")
    headers   = {"Authorization": f"Bearer {token_jwt}"} if token_jwt else {}
    try:
        r = httpx.get(f"{API_V1}/invites/", headers=headers, timeout=5.0)
        if r.status_code == 200:
            convites_sessao = [{**inv, "origem": "api"} for inv in r.json()]
    except Exception:
        pass

if not convites_sessao:
    components.empty_state(
        icon="📨",
        title="Nenhum convite gerado ainda",
        message="Use o formulário acima para gerar o primeiro convite.",
    )
else:
    for inv in convites_sessao:
        email_inv  = inv.get("email", "N/A")
        role_inv   = inv.get("role", "b2b")
        usado      = inv.get("used", False)
        origem_inv = inv.get("origem", "offline")
        status_str = "✅ Usado" if usado else "⏳ Pendente"
        expira     = inv.get("expires_at", "")
        url_inv    = inv.get("signup_url", "")

        with st.expander(f"{email_inv}  —  {status_str}  ·  {_badge_role(role_inv)}"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**Perfil:** {_badge_role(role_inv)}")
                st.markdown(f"**Status:** {status_str}")
                st.markdown(f"**Expira em:** {expira}")
                st.markdown(f"**Origem:** {_badge_origem(origem_inv)}")
            with col_b:
                st.markdown(f"**Token:** `{inv.get('token', 'N/A')}`")
                if url_inv:
                    st.markdown(f"**Link de cadastro:**")
                    st.code(url_inv, language=None)
