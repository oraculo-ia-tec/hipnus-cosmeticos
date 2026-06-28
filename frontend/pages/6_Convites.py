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

st.set_page_config(page_title="Convites · HIPNUS", page_icon="✉️", layout="wide")
ui.inject_theme()
usuario = require_auth(perfis_permitidos=["super_admin", "admin"])
build_sidebar()

components.page_header(
    title="Convites de Parceiros",
    subtitle="Gerencie os acessos B2B da plataforma.",
    kicker="✉️ Gestão de Acessos",
)

tab_novo, tab_lista = st.tabs(["➕ Novo Convite", "📋 Lista de Convites"])

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

with tab_lista:
    try:
        invites = listar_invites_db()
    except Exception as exc:
        st.error(f"Erro ao listar convites: {exc}")
        invites = []

    if not invites:
        components.empty_state(icon="✉️", title="Nenhum convite", message="Crie o primeiro convite na aba ao lado.")
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
                st.markdown(f"**{email_inv}** · `{role_inv}` · Expira: {expires} · {badge}")
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
