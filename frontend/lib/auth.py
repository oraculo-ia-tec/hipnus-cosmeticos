"""
auth.py — HIPNUS COSMÉTICOS
==============================
Guarda de autenticação.

Navegação (caminhos registrados pelo Streamlit Cloud):
  Login     → "streamlit_app.py"
  Home      → "pages/1_Home.py"

Roles: super_admin, admin, b2b, b2c, demo
"""
from __future__ import annotations

import httpx
import streamlit as st
from lib.config import API_V1

ROLES_PRIVILEGIADOS = {"super_admin", "admin"}
ROLES_PROFISSIONAIS = {"super_admin", "admin", "b2b"}


def login_via_api(username: str, password: str) -> dict | None:
    try:
        r = httpx.post(
            f"{API_V1}/auth/login",
            data={"username": username, "password": password},
            timeout=5.0,
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


USUARIOS_DEMO = {
    "william": {"senha": "hipnus@2026", "role": "super_admin", "nome": "William Eustáquio",
                "display_name": "Desenvolvedor de IA", "email": "programador.descpro@gmail.com"},
    "admin":   {"senha": "hipnus@adm",  "role": "admin",       "nome": "Administrador",
                "display_name": "Admin Hipnus", "email": "admin@hipnuscosmeticos.com.br"},
    "pro":     {"senha": "hipnus@pro",  "role": "b2b",         "nome": "Profissional",
                "display_name": "Profissional B2B", "email": "pro@hipnuscosmeticos.com.br"},
    "user":    {"senha": "hipnus@user", "role": "b2c",         "nome": "Cliente",
                "display_name": "Cliente B2C", "email": "user@hipnuscosmeticos.com.br"},
}


def _login_offline(username: str, password: str) -> bool:
    u = USUARIOS_DEMO.get(username.strip().lower())
    if not u or password != u["senha"]:
        return False
    _gravar_sessao(
        nome=u["nome"], username=username.lower(), role=u["role"],
        display_name=u["display_name"], email=u["email"], token=None, via_api=False,
    )
    return True


def _gravar_sessao(nome, username, role, display_name, email, token, via_api):
    st.session_state.update({
        "autenticado": True, "usuario": username, "nome": nome,
        "perfil": role, "display_name": display_name,
        "email": email, "token": token, "via_api": via_api,
    })


def fazer_login(username: str, password: str) -> tuple[bool, str]:
    resultado = login_via_api(username, password)
    if resultado:
        user = resultado["user"]
        _gravar_sessao(
            nome=user["name"], username=user["username"], role=user["role"],
            display_name=user.get("display_name") or user["name"],
            email=user["email"], token=resultado["access_token"], via_api=True,
        )
        return True, f"Bem-vindo(a), {user['name']}!"

    if _login_offline(username, password):
        nome = USUARIOS_DEMO[username.strip().lower()]["nome"]
        return True, f"Bem-vindo(a), {nome}!"

    return False, "Usuário ou senha incorretos."


def require_auth(perfis_permitidos: list[str] | None = None) -> dict:
    if not st.session_state.get("autenticado"):
        st.switch_page("streamlit_app.py")

    usuario = {
        "login":        st.session_state.get("usuario", ""),
        "perfil":       st.session_state.get("perfil",  "demo"),
        "nome":         st.session_state.get("nome",    "Visitante"),
        "display_name": st.session_state.get("display_name", ""),
        "email":        st.session_state.get("email",   ""),
        "token":        st.session_state.get("token",   None),
        "via_api":      st.session_state.get("via_api", False),
    }

    if perfis_permitidos and usuario["perfil"] not in perfis_permitidos:
        st.error("🚫 Você não tem permissão para acessar esta página.")
        st.stop()

    return usuario


def logout() -> None:
    for key in ["autenticado", "usuario", "perfil", "nome", "display_name", "email", "token", "via_api"]:
        st.session_state.pop(key, None)
    st.switch_page("streamlit_app.py")


def sidebar_user_info() -> None:
    nome         = st.session_state.get("nome", "Visitante")
    display_name = st.session_state.get("display_name", "")
    perfil       = st.session_state.get("perfil", "demo")
    via_api      = st.session_state.get("via_api", False)

    icone = {"super_admin": "⭐", "admin": "🛡️", "b2b": "🏪", "b2c": "👤", "demo": "👀"}.get(perfil, "👤")
    fonte = "🔗 API" if via_api else "📴 offline"
    label = display_name if display_name else nome

    st.sidebar.markdown(
        f"**{icone} {label}**  \n"
        f"<span style='font-size:0.78rem; color:#6B6580;'>Perfil: **{perfil.upper()}** &nbsp;·&nbsp; {fonte}</span>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sair", use_container_width=True):
        logout()
