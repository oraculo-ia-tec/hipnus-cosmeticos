"""
auth.py — HIPNUS COSMÉTICOS
==============================
Guarda de autenticação para páginas protegidas.

Fluxo:
  - Se o backend estiver online: login via API (/auth/login) com JWT real.
  - Se o backend estiver offline: fallback para usuários locais de demo.

Roles (mapeados do campo `role` do JWT):
  super_admin — acesso total
  admin       — administrador operacional  
  b2b         — profissional / salão / distribuidor
  b2c         — consumidor final
  demo        — visitante sem login (somente leitura)
"""
from __future__ import annotations

import httpx
import streamlit as st
from lib.config import API_V1


# ─── Roles privilegiados ─────────────────────────────────────────────
ROLES_PRIVILEGIADOS = {"super_admin", "admin"}
ROLES_PROFISSIONAIS = {"super_admin", "admin", "b2b"}


# ─── Autenticação via API ───────────────────────────────────────────
def login_via_api(username: str, password: str) -> dict | None:
    """
    Autentica o usuário via API FastAPI.
    Retorna o dicionário com `token` e `user` se bem-sucedido, None se falhar.
    """
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


# ─── Fallback offline ───────────────────────────────────────────────
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
    """Fallback: autentica contra usuários locais quando a API está offline."""
    u = USUARIOS_DEMO.get(username.strip().lower())
    if not u or password != u["senha"]:
        return False
    _gravar_sessao(
        nome=u["nome"],
        username=username.lower(),
        role=u["role"],
        display_name=u["display_name"],
        email=u["email"],
        token=None,
        via_api=False,
    )
    return True


# ─── Sessão ──────────────────────────────────────────────────────────────
def _gravar_sessao(nome, username, role, display_name, email, token, via_api):
    st.session_state["autenticado"]   = True
    st.session_state["usuario"]       = username
    st.session_state["nome"]          = nome
    st.session_state["perfil"]        = role
    st.session_state["display_name"]  = display_name
    st.session_state["email"]         = email
    st.session_state["token"]         = token
    st.session_state["via_api"]       = via_api


def fazer_login(username: str, password: str) -> tuple[bool, str]:
    """
    Tenta autenticar via API; se offline, usa fallback local.
    Retorna (sucesso: bool, mensagem: str).
    """
    resultado = login_via_api(username, password)
    if resultado:
        user = resultado["user"]
        _gravar_sessao(
            nome=user["name"],
            username=user["username"],
            role=user["role"],
            display_name=user.get("display_name") or user["name"],
            email=user["email"],
            token=resultado["access_token"],
            via_api=True,
        )
        return True, f"Bem-vindo(a), {user['name']}!"

    # Fallback offline
    if _login_offline(username, password):
        return True, "Login offline (modo demonstração)."

    return False, "Usuário ou senha incorretos."


# ─── Guards ──────────────────────────────────────────────────────────────
def require_auth(perfis_permitidos: list[str] | None = None) -> dict:
    """
    Verifica autenticação. Redireciona para Login se não autenticado.
    Bloqueia perfis não autorizados se perfis_permitidos for informado.
    Retorna dicionário com dados do usuário logado.
    """
    if not st.session_state.get("autenticado"):
        st.switch_page("Login.py")

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
    """Encerra a sessão e redireciona para Login."""
    for key in ["autenticado", "usuario", "perfil", "nome", "display_name", "email", "token", "via_api"]:
        st.session_state.pop(key, None)
    st.switch_page("Login.py")


def sidebar_user_info() -> None:
    """Exibe informações do usuário logado e botão de logout na sidebar."""
    nome         = st.session_state.get("nome", "Visitante")
    display_name = st.session_state.get("display_name", "")
    perfil       = st.session_state.get("perfil", "demo")
    via_api      = st.session_state.get("via_api", False)

    icone = {
        "super_admin": "⭐",
        "admin":       "🛡️",
        "b2b":         "🏪",
        "b2c":         "👤",
        "demo":        "👀",
    }.get(perfil, "👤")

    fonte = "🔗 API" if via_api else "📴 offline"

    label = display_name if display_name else nome
    st.sidebar.markdown(
        f"**{icone} {label}**  \n"
        f"<span style='font-size:0.78rem; color:#6B6580;'>"
        f"Perfil: **{perfil.upper()}** &nbsp;·&nbsp; {fonte}"
        f"</span>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sair", use_container_width=True):
        logout()
