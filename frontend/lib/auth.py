"""
auth.py — HIPNUS COSMÉTICOS
==============================
Guarda de autenticação + Sidebar Premium Unificada.
"""
from __future__ import annotations

import streamlit as st

ROLES_PRIVILEGIADOS = {"super_admin", "admin"}
ROLES_PROFISSIONAIS = {"super_admin", "admin", "b2b"}

LOGIN_PAGE  = "streamlit_app.py"
HOME_PAGE   = "pages/1_Home.py"
_LOGIN_PAGE = LOGIN_PAGE
_HOME_PAGE  = HOME_PAGE


# ─── Usuários demo/seed ─────────────────────────────────────────────────────
USUARIOS_DEMO: dict[str, dict] = {
    "william": {
        "senha":        "hipnus@2026",
        "role":         "super_admin",
        "nome":         "William Eustáquio",
        "display_name": "Desenvolvedor de IA",
        "email":        "programador.descpro@gmail.com",
    },
    "williamllider": {
        "senha":        "teste@123",
        "role":         "b2b",
        "nome":         "William Llider",
        "display_name": "Parceiro B2B",
        "email":        "williamllider@gmail.com",
    },
    "admin": {
        "senha":        "hipnus@adm",
        "role":         "admin",
        "nome":         "Administrador",
        "display_name": "Admin Hipnus",
        "email":        "admin@hipnuscosmeticos.com.br",
    },
    "pro": {
        "senha":        "hipnus@pro",
        "role":         "b2b",
        "nome":         "Profissional",
        "display_name": "Profissional B2B",
        "email":        "pro@hipnuscosmeticos.com.br",
    },
    "user": {
        "senha":        "hipnus@user",
        "role":         "b2c",
        "nome":         "Cliente",
        "display_name": "Cliente B2C",
        "email":        "user@hipnuscosmeticos.com.br",
    },
}


# ─── Helpers de sessão ────────────────────────────────────────────────────
def _gravar_sessao(
    nome: str, username: str, role: str,
    display_name: str, email: str, token: str | None,
    via_api: bool, avatar_b64: str | None = None,
) -> None:
    import time
    st.session_state.update({
        "autenticado":       True,
        "usuario":           username,
        "nome":              nome,
        "perfil":            role,
        "display_name":      display_name,
        "email":             email,
        "token":             token,
        "via_api":           via_api,
        "avatar_b64":        avatar_b64,
        "session_start":     time.time(),
        "_jwt_dialog_shown": False,
    })


def _buscar_demo(identificador: str) -> tuple[str, dict] | None:
    ident = identificador.strip().lower()
    if ident in USUARIOS_DEMO:
        return ident, USUARIOS_DEMO[ident]
    for uname, dados in USUARIOS_DEMO.items():
        if dados.get("email", "").lower() == ident:
            return uname, dados
    return None


def _buscar_parceiro_db(email: str, senha: str) -> dict | None:
    try:
        import sys
        from pathlib import Path
        _root = Path(__file__).resolve().parents[2]
        if str(_root) not in sys.path:
            sys.path.insert(0, str(_root))
        from lib.user_db import autenticar_parceiro
        result = autenticar_parceiro(email, senha)
        if result:
            return result
    except Exception:
        pass
    try:
        from lib.db_utils import get_db_session
        from sqlalchemy import text
        db, _ = get_db_session()
        if not db:
            return None
        try:
            row = db.execute(
                text("SELECT email, role FROM invites WHERE email = :e AND used = 1 LIMIT 1"),
                {"e": email.lower().strip()},
            ).fetchone()
            if row:
                d = dict(row._mapping)
                nome_base = email.split("@")[0].capitalize()
                return {
                    "nome": nome_base, "username": d["email"],
                    "role": d.get("role", "b2b"), "display_name": nome_base,
                    "email": d["email"], "avatar_b64": None,
                }
        finally:
            db.close()
    except Exception:
        pass
    return None


def _login_offline(identificador: str, password: str) -> bool:
    encontrado = _buscar_demo(identificador)
    if encontrado:
        uname, u = encontrado
        if password == u["senha"]:
            _gravar_sessao(
                nome=u["nome"], username=uname, role=u["role"],
                display_name=u["display_name"], email=u["email"],
                token=None, via_api=False, avatar_b64=None,
            )
            return True
        return False
    if "@" in identificador:
        parceiro = _buscar_parceiro_db(identificador, password)
        if parceiro:
            _gravar_sessao(
                nome=parceiro.get("nome", ""),
                username=parceiro.get("username") or parceiro.get("email", ""),
                role=parceiro.get("role", "b2b"),
                display_name=parceiro.get("display_name") or parceiro.get("empresa") or parceiro.get("nome", ""),
                email=parceiro.get("email", ""),
                token=None, via_api=False,
                avatar_b64=parceiro.get("avatar_b64"),
            )
            return True
    return False


def fazer_login(identificador: str, password: str) -> tuple[bool, str]:
    if _login_offline(identificador, password):
        encontrado = _buscar_demo(identificador)
        nome = encontrado[1]["nome"] if encontrado else identificador.split("@")[0].capitalize()
        return True, f"Bem-vindo(a), {nome}!"
    return False, "Usuário/e-mail ou senha incorretos."


def require_auth(perfis_permitidos: list[str] | None = None) -> dict:
    if st.query_params.get("logout") == "1":
        logout()
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
        "avatar_b64":   st.session_state.get("avatar_b64", None),
    }
    if perfis_permitidos and usuario["perfil"] not in perfis_permitidos:
        st.error("�edd5 Você não tem permissão para acessar esta página.")
        st.stop()
    return usuario


def logout() -> None:
    for key in [
        "autenticado", "usuario", "perfil", "nome",
        "display_name", "email", "token", "via_api", "avatar_b64",
        "session_start", "_jwt_dialog_shown",
    ]:
        st.session_state.pop(key, None)
    st.query_params.clear()
    st.switch_page(_LOGIN_PAGE)


# ───────────────────────────────────────────────────────────────────────
# SIDEBAR PREMIUM — componentes reutilizáveis
# ───────────────────────────────────────────────────────────────────────

def sidebar_logo() -> None:
    """Logo HIPNUS no topo da sidebar."""
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
    """Card premium do usuário logado na sidebar."""
    nome         = st.session_state.get("nome", "Visitante")
    display_name = st.session_state.get("display_name", "")
    perfil       = st.session_state.get("perfil", "demo")
    via_api      = st.session_state.get("via_api", False)
    avatar_b64   = st.session_state.get("avatar_b64", None)

    icones = {"super_admin": "⭐", "admin": "🛡️", "b2b": "🎤", "b2c": "👤", "demo": "👀"}
    icone_fallback = icones.get(perfil, "👤")
    fonte      = "API" if via_api else "offline"
    label      = display_name if display_name else nome
    role_label = perfil.replace("_", " ").upper()

    if avatar_b64:
        avatar_html = (
            f'<img src="{avatar_b64}" '
            'style="width:44px;height:44px;border-radius:50%;object-fit:cover;'
            'border:2px solid rgba(185,131,255,.5);flex-shrink:0;" />'
        )
    else:
        avatar_html = (
            f'<div style="width:44px;height:44px;border-radius:50%;'
            'background:linear-gradient(135deg,rgba(124,58,237,.4),rgba(185,131,255,.2));'
            'border:2px solid rgba(185,131,255,.4);'
            'display:flex;align-items:center;justify-content:center;'
            f'font-size:1.3rem;flex-shrink:0;">{icone_fallback}</div>'
        )

    st.sidebar.html(f"""
    <div style="padding:0 4px 8px;">
      <div style="
        display:flex;align-items:center;gap:10px;
        background:linear-gradient(135deg,rgba(124,58,237,.2),rgba(185,131,255,.08));
        border:1px solid rgba(185,131,255,.3);
        border-radius:14px;padding:10px 12px;
        transition:all .2s ease;
      ">
        {avatar_html}
        <div style="min-width:0;flex:1;">
          <div style="font-weight:700;font-size:.88rem;color:#fff;
                      white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
                      max-width:140px;line-height:1.3;"
               title="{label}">{label}</div>
          <div style="display:flex;gap:5px;margin-top:5px;flex-wrap:wrap;align-items:center;">
            <span style="background:linear-gradient(135deg,rgba(124,58,237,.6),rgba(91,33,182,.8));
                         color:#e9d5ff;font-size:.58rem;font-weight:700;
                         letter-spacing:.8px;padding:2px 9px;border-radius:999px;
                         text-transform:uppercase;">{role_label}</span>
            <span style="color:rgba(185,131,255,.5);font-size:.58rem;">• {fonte}</span>
          </div>
        </div>
      </div>
    </div>
    """)


def sidebar_section_label(label: str) -> None:
    """Cabeçalho de grupo de seção na sidebar."""
    st.sidebar.html(f"""
    <div style="
      padding: 10px 16px 4px;
      font-family:'Inter',sans-serif;
      font-size:.6rem;font-weight:700;
      letter-spacing:1.8px;text-transform:uppercase;
      color:rgba(185,131,255,.45);
      line-height:1;
    ">{label}</div>
    """)


def sidebar_divider() -> None:
    """Separador visual neon entre seções da sidebar."""
    st.sidebar.html("""
    <div style="
      margin:8px 16px;
      height:1px;
      background:linear-gradient(90deg,transparent,rgba(185,131,255,.25),transparent);
    "></div>
    """)


def sidebar_nav_highlight() -> None:
    """CSS extra para garantir que os links do nav nativo fiquem legíveis e elegantes."""
    st.sidebar.html("""
    <style>
    /* ─ Nav links: força cor branca e espaçamento ─ */
    [data-testid="stSidebarNavLink"] {
      color: rgba(255,255,255,.82) !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 500 !important;
      font-size: .88rem !important;
      padding: 9px 16px !important;
      border-radius: 10px !important;
      margin: 1px 6px !important;
      border: 1px solid transparent !important;
      transition: all .2s ease !important;
      letter-spacing: .1px !important;
      display: flex !important;
      align-items: center !important;
      gap: 8px !important;
    }
    [data-testid="stSidebarNavLink"]:hover {
      color: #fff !important;
      background: rgba(185,131,255,.14) !important;
      border-color: rgba(185,131,255,.28) !important;
      text-shadow: 0 0 10px rgba(185,131,255,.4) !important;
    }
    [data-testid="stSidebarNavLink"][aria-current="page"] {
      color: #fff !important;
      background: rgba(124,58,237,.28) !important;
      border-color: rgba(185,131,255,.45) !important;
      box-shadow: 0 0 14px rgba(185,131,255,.18) !important;
      font-weight: 600 !important;
    }
    /* ─ Sidebar nav list: padding uniforme ─ */
    [data-testid="stSidebarNavItems"] {
      padding: 4px 0 8px !important;
    }
    [data-testid="stSidebarNavItems"] li {
      margin: 0 !important;
    }
    /* ─ Textos e captions da sidebar ─ */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {
      color: rgba(255,255,255,.75) !important;
    }
    section[data-testid="stSidebar"] strong {
      color: #fff !important;
    }
    </style>
    """)


def sidebar_logout_button() -> None:
    """Botão fixo Sair no rodapé da sidebar."""
    st.sidebar.html("""
    <style>
    #hip-logout-btn-wrap {
      position: fixed; bottom: 18px; left: 0;
      width: 244px; padding: 0 14px;
      z-index: 99999; box-sizing: border-box;
    }
    #hip-logout-btn {
      display: flex; align-items: center; justify-content: center;
      gap: 8px; width: 100%; padding: 11px 0;
      background: rgba(255,255,255,.06);
      color: rgba(255,255,255,.8);
      border: 1px solid rgba(185,131,255,.25);
      border-radius: 12px;
      font-family: 'Inter', sans-serif;
      font-size: .88rem; font-weight: 600;
      cursor: pointer; letter-spacing: .01em;
      box-sizing: border-box;
      transition: all .18s ease;
      text-decoration: none;
    }
    #hip-logout-btn:hover {
      background: rgba(185,131,255,.18);
      color: #fff;
      border-color: rgba(185,131,255,.5);
      box-shadow: 0 0 18px rgba(185,131,255,.2);
    }
    </style>
    <div id="hip-logout-btn-wrap">
      <a id="hip-logout-btn" href="?logout=1"
         onclick="window.parent.location.href='?logout=1'; return false;">
        🚶 Sair
      </a>
    </div>
    """)


# ─── Função unificada: monta toda a sidebar de uma vez ────────────────────────────
def build_sidebar(
    show_cart: bool = True,
    cart_count: int = 0,
    cart_total: float = 0.0,
) -> None:
    """
    Monta a sidebar premium completa em ordem:
      1. Logo HIPNUS
      2. Card do usuário
      3. CSS nav highlight
      4. [Menu nativo Streamlit — automático]
      5. Separador
      6. Resumo do carrinho (opcional)
      7. Botão Sair (fixo no rodapé)
    """
    sidebar_logo()
    sidebar_user_info()
    sidebar_nav_highlight()
    if show_cart and cart_count > 0:
        sidebar_divider()
        from .ui import brl
        st.sidebar.html(f"""
        <div style="
          margin:4px 10px 6px;
          background:rgba(124,58,237,.12);
          border:1px solid rgba(185,131,255,.2);
          border-radius:10px;padding:8px 12px;
          display:flex;justify-content:space-between;align-items:center;
        ">
          <span style="color:rgba(255,255,255,.7);font-size:.78rem;">🛒 Carrinho</span>
          <span style="color:#fff;font-weight:700;font-size:.82rem;">{brl(cart_total)}</span>
        </div>
        """)
    sidebar_logout_button()
