"""
7_Cadastro_Parceiro.py — HIPNUS COSMÉTICOS
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
from lib.user_db import cadastrar_parceiro, listar_parceiros, deletar_parceiro

st.set_page_config(page_title="Cadastro Parceiro · HIPNUS", page_icon="➕", layout="wide")
ui.inject_theme()
usuario = require_auth(perfis_permitidos=["super_admin", "admin"])
build_sidebar()

components.page_header(
    title="Cadastro de Parceiros",
    subtitle="Adicione e gerencie os parceiros B2B da plataforma.",
    kicker="➕ Gestão de Parceiros",
)

tab_novo, tab_lista = st.tabs(["➕ Novo Parceiro", "👥 Lista de Parceiros"])

with tab_novo:
    with st.form("form_parceiro"):
        nome   = st.text_input("Nome completo")
        email  = st.text_input("E-mail")
        senha  = st.text_input("Senha", type="password")
        perfil = st.selectbox("Perfil", ["b2b", "b2c", "admin"])
        cidade = st.text_input("Cidade")
        estado = st.text_input("Estado (UF)")
        submit = st.form_submit_button("Cadastrar", use_container_width=True)
    if submit:
        if not nome or not email or not senha:
            st.error("Preencha nome, e-mail e senha.")
        else:
            try:
                cadastrar_parceiro(
                    nome=nome, email=email, senha=senha,
                    perfil=perfil, cidade=cidade, estado=estado,
                )
                st.success(f"✅ Parceiro **{nome}** cadastrado com sucesso!")
            except Exception as exc:
                st.error(f"Erro: {exc}")

with tab_lista:
    try:
        parceiros = listar_parceiros()
    except Exception as exc:
        st.error(f"Erro ao listar: {exc}")
        parceiros = []

    if not parceiros:
        components.empty_state(icon="👥", title="Nenhum parceiro", message="Cadastre o primeiro parceiro na aba ao lado.")
    else:
        for p in parceiros:
            c1, c2 = st.columns([4, 1])
            with c1:
                loc = f"{p.get('cidade','')}/{p.get('estado','')}" if p.get('cidade') else p.get('estado', '—')
                st.markdown(f"**{p.get('nome','')}** · `{p.get('email','')}` · {p.get('perfil','').upper()} · {loc}")
            with c2:
                if st.button("🗑️ Remover", key=f"del_p_{p.get('email','')}"):
                    try:
                        deletar_parceiro(p.get("email", ""))
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
