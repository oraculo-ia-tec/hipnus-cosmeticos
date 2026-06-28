"""
6_Convites.py — HIPNUS COSMÉTICOS
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
from lib.invite_db import (
    criar_invite_db, listar_invites_db,
    deletar_invite_db, reativar_invite_db,
)
from lib.email_service import send_invite_email, smtp_status

st.set_page_config(page_title="Convites · HIPNUS", page_icon="✉️", layout="wide")
ui.inject_theme()
usuario = require_auth(perfis_permitidos=["super_admin", "admin"])
build_sidebar()

components.page_header(
    title="Convites de Parceiros",
    subtitle="Gerencie os acessos B2B da plataforma.",
    kicker="✉️ Gestão de Acessos",
)

# URL base para o link de cadastro (ajuste conforme o domínio)
_DEFAULT_SIGNUP_URL = "https://hipnuscosmeticos.com.br/cadastro"

tab_novo, tab_email, tab_lista = st.tabs([
    "➕ Novo Convite",
    "📧 Enviar por E-mail",
    "📋 Lista de Convites",
])

# ── Aba 1: Gerar token (sem envio) ─────────────────────────────────────────────────
with tab_novo:
    with st.form("form_convite"):
        email   = st.text_input("E-mail do parceiro")
        role    = st.selectbox("Perfil", ["b2b", "b2c", "admin"])
        dias    = st.number_input("Validade (dias)", min_value=1, max_value=365, value=30)
        submit  = st.form_submit_button("Gerar Convite", use_container_width=True)
    if submit:
        if not email or "@" not in email:
            st.error("Informe um e-mail válido.")
        else:
            try:
                token = criar_invite_db(email=email, role=role, dias=int(dias))
                st.success(f"✅ Convite gerado para **{email}**")
                st.code(token, language="text")
            except Exception as exc:
                st.error(f"Erro ao criar convite: {exc}")

# ── Aba 2: Gerar + Enviar por E-mail ──────────────────────────────────────────────
with tab_email:
    # Diagnóstico SMTP discreto
    smtp = smtp_status()
    if not smtp["ready"]:
        st.warning(
            "🚨 **SMTP não configurado.** "
            "Adicione `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USERNAME` e `EMAIL_PASSWORD` "
            "nos Secrets do Streamlit para habilitar o envio.",
        )
    else:
        st.success(f"✅ SMTP pronto · Remetente: `{smtp['from_email']}`")

    st.markdown("### Enviar convite de cadastro por e-mail")
    st.caption(
        "Gera um token único, monta o link de cadastro e dispara o e-mail com template visual."
    )

    with st.form("form_convite_email"):
        email_dest  = st.text_input("📧 E-mail do convidado", placeholder="parceiro@email.com")
        role_dest   = st.selectbox("Perfil", ["b2b", "b2c", "admin"], key="role_email")
        dias_dest   = st.number_input(
            "Validade (dias)", min_value=1, max_value=365, value=30, key="dias_email"
        )
        signup_base = st.text_input(
            "URL base de cadastro",
            value=_DEFAULT_SIGNUP_URL,
            help="O token será adicionado como parâmetro ?token=...",
        )
        enviar = st.form_submit_button(
            "📤 Gerar token e enviar e-mail",
            use_container_width=True,
            disabled=not smtp["ready"],
        )

    if enviar:
        if not email_dest or "@" not in email_dest:
            st.error("Informe um e-mail válido.")
        else:
            try:
                # 1. Gera o token no banco
                token = criar_invite_db(
                    email=email_dest,
                    role=role_dest,
                    dias=int(dias_dest),
                )
                # 2. Monta o link completo
                signup_url = f"{signup_base.rstrip('/')}?token={token}"
                # 3. Dispara o e-mail
                with st.spinner("Enviando e-mail..."):
                    ok, msg = send_invite_email(
                        destinatario=email_dest,
                        signup_url=signup_url,
                        role=role_dest,
                    )
                if ok:
                    st.success(f"✅ Convite enviado para **{email_dest}**!")
                    st.info(🔗 Link gerado: `{signup_url}`")
                else:
                    st.error(f"❌ Falha ao enviar e-mail: {msg}")
                    st.code(token, language="text")
                    st.caption("Copie o token acima e envie manualmente.")
            except Exception as exc:
                st.error(f"Erro: {exc}")

# ── Aba 3: Lista de convites ─────────────────────────────────────────────────────────
with tab_lista:
    try:
        invites = listar_invites_db()
    except Exception as exc:
        st.error(f"Erro ao listar convites: {exc}")
        invites = []

    if not invites:
        components.empty_state(
            icon="✉️",
            title="Nenhum convite",
            message="Crie o primeiro convite nas abas ao lado.",
        )
    else:
        for inv in invites:
            usado     = inv.get("used", False)
            email_inv = inv.get("email", "")
            token_inv = inv.get("token", "")
            expires   = str(inv.get("expires_at") or "")[:10]
            role_inv  = inv.get("role", "")

            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                badge = "✅ Usado" if usado else "⏳ Ativo"
                st.markdown(
                    f"**{email_inv}** · `{role_inv}` · Expira: {expires} · {badge}"
                )
            with c2:
                if usado and st.button("🔄 Reativar", key=f"reat_{token_inv}"):
                    try:
                        reativar_invite_db(token_inv, dias=30)
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
            with c3:
                if st.button("🗑️ Deletar", key=f"del_{token_inv}"):
                    try:
                        deletar_invite_db(token_inv)
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
