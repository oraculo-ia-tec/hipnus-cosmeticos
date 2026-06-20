"""
auth.py — HIPNUS COSMÉTICOS
==============================
Guarda de autenticação.

Navegação (caminhos reais do Streamlit Cloud):
  Login     →  "streamlit_app.py"      ← entrypoint real (raiz do repo)
  Home      →  "pages/1_Home.py"

Roles: super_admin, admin, b2b, b2c, demo

Ordem da sidebar (convenção entre todas as páginas):
  1. sidebar_logo()             → logo Hipnus SVG (TOPO — nova função)
  2. sidebar_user_info()        → card do usuário logado (ACIMA do menu)
  3. [menu nativo Streamlit]    → renderizado automaticamente
  4. ui.api_status_badge()      → status da API
  5. ui.sidebar_cart_summary()  → resumo do carrinho
  6. sidebar_logout_button()    → botão SAIR (ABAIXO do menu)
"""
from __future__ import annotations

import httpx
import streamlit as st
from lib.config import API_V1

ROLES_PRIVILEGIADOS = {"super_admin", "admin"}
ROLES_PROFISSIONAIS = {"super_admin", "admin", "b2b"}

# ─ Entrypoint real do Streamlit Cloud ────────────────────────────────
# streamlit_app.py está na RAIZ do repo — é o entrypoint que o Streamlit
# Cloud usa. Todos os switch_page de logout/require_auth apontam para ele.
_LOGIN_PAGE = "streamlit_app.py"
_HOME_PAGE  = "pages/1_Home.py"


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
    """Protege a página exigindo autenticação.

    Se não autenticado, redireciona para streamlit_app.py (entrypoint real).
    Se perfis_permitidos for informado, bloqueia perfis não autorizados.
    """
    if not st.session_state.get("autenticado"):
        st.switch_page(_LOGIN_PAGE)

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
    """Limpa a sessão e redireciona para o login (streamlit_app.py)."""
    for key in ["autenticado", "usuario", "perfil", "nome", "display_name", "email", "token", "via_api"]:
        st.session_state.pop(key, None)
    st.switch_page(_LOGIN_PAGE)


def sidebar_logo() -> None:
    """Renderiza o logo HIPNUS COSMÉTICOS no topo da sidebar.

    DEVE ser a PRIMEIRA chamada de sidebar em cada página,
    antes de sidebar_user_info() e do menu nativo.
    Substitui brand_header() com visual mais premium.
    """
    st.sidebar.html("""
    <div class="hip-sidebar-logo-wrap">
        <div class="hip-sidebar-logo-icon">H</div>
        <div class="hip-sidebar-logo-text">
            <div class="l1">HIPNUS</div>
            <div class="l2">Cosm&eacute;ticos</div>
        </div>
    </div>
    """)


def sidebar_user_info() -> None:
    """Card compacto do usuário logado na sidebar.

    Deve ser chamado IMEDIATAMENTE APÓS sidebar_logo(), antes do
    conteúdo da página, para que o Streamlit o posicione acima do menu
    nativo de navegação.
    NÃO inclui o botão Sair — use sidebar_logout_button() no final.
    """
    nome         = st.session_state.get("nome", "Visitante")
    display_name = st.session_state.get("display_name", "")
    perfil       = st.session_state.get("perfil", "demo")
    via_api      = st.session_state.get("via_api", False)

    icone = {"super_admin": "⭐", "admin": "🛡️", "b2b": "🎤", "b2c": "👤", "demo": "👀"}.get(perfil, "👤")
    fonte = "API" if via_api else "offline"
    label = display_name if display_name else nome

    st.sidebar.html(
        f"""
        <div class="hip-sidebar-user">
            <div class="uname">{icone}&nbsp;{label}</div>
            <div class="umeta">
                <span class="badge-role">{perfil.replace('_', ' ').upper()}</span>
                <span class="badge-src">{fonte}</span>
            </div>
        </div>
        """
    )


def sidebar_logout_button() -> None:
    """Botão SAIR da sidebar.

    Deve ser a última chamada de sidebar em cada página,
    posicionado abaixo do menu nativo de navegação.
    """
    st.sidebar.markdown("---")
    if st.sidebar.button("🚶 Sair", use_container_width=True, key="btn_logout_global"):
        logout()
