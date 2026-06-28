"""
9_Usuarios.py — HIPNUS COSMÉTICOS
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
from lib.user_db import listar_parceiros, deletar_parceiro

st.set_page_config(page_title="Usuários · HIPNUS", page_icon="👥", layout="wide")
ui.inject_theme()
usuario = require_auth(perfis_permitidos=["super_admin"])
build_sidebar()

components.page_header(
    title="Usuários",
    subtitle="Gerencie todos os usuários da plataforma.",
    kicker="👥 Administração",
)

try:
    usuarios = listar_parceiros()
except Exception as exc:
    st.error(f"Erro ao carregar usuários: {exc}")
    usuarios = []

if not usuarios:
    components.empty_state(icon="👥", title="Nenhum usuário", message="Cadastre parceiros na página de Cadastro.")
else:
    st.caption(f"{len(usuarios)} usuário(s) cadastrado(s)")
    for u in usuarios:
        c1, c2 = st.columns([4, 1])
        with c1:
            loc = f"{u.get('cidade','')}/{u.get('estado','')}" if u.get('cidade') else u.get('estado', '—')
            st.markdown(f"**{u.get('nome','')}** · `{u.get('email','')}` · {u.get('perfil','').upper()} · {loc}")
        with c2:
            if st.button("🗑️ Remover", key=f"del_u_{u.get('email','')}"):
                try:
                    deletar_parceiro(u.get("email", ""))
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
