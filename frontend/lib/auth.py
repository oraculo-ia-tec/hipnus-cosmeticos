"""
auth.py — HIPNUS COSMÉTICOS
==============================
Guarda de autenticação + Sidebar Pro Redesign.
"""
from __future__ import annotations

import streamlit as st

ROLES_PRIVILEGIADOS = {"super_admin", "admin"}
ROLES_PROFISSIONAIS = {"super_admin", "admin", "b2b"}

LOGIN_PAGE  = "streamlit_app.py"
HOME_PAGE   = "pages/1_Home.py"
_LOGIN_PAGE = LOGIN_PAGE
_HOME_PAGE  = HOME_PAGE


# ─── Usuários demo/seed ──────────────────────────────────────────────
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


# ─── Helpers de sessão ────────────────────────────────────────────
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
        st.error("🚫 Você não tem permissão para acessar esta página.")
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
# SIDEBAR PRO REDESIGN 2026
# ───────────────────────────────────────────────────────────────────────

# Mapa de página → (ícone SVG inline, label display, grupos)
_NAV_ITEMS = [
    # grupo, page_key, label, icon_svg
    ("ai",   "11_IA_Consultora",  "IA Consultora",    "brain"),
    ("main", "1_Home",            "Home",             "home"),
    ("main", "0_Dashboard",       "Dashboard",        "chart"),
    ("shop", "2_Catalogo",        "Catálogo",         "grid"),
    ("shop", "3_Linhas",          "Linhas",           "sparkles"),
    ("shop", "4_Loja_Parceiro",   "Loja Parceiro",    "store"),
    ("shop", "5_Carrinho",        "Carrinho",         "cart"),
    ("shop", "6_Checkout",        "Checkout",         "creditcard"),
    ("mgmt", "7_Convites",        "Convites",         "mail"),
    ("mgmt", "8_Cadastro_Parceiro","Cadastro",        "userplus"),
    ("mgmt", "9_Configuracao",    "Configurações",    "settings"),
    ("mgmt", "10_Usuarios",       "Usuários",         "users"),
]

_ICONS = {
    "brain":      '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-2.66z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-2.66z"/></svg>',
    "home":       '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
    "chart":      '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/><line x1="2" y1="20" x2="22" y2="20"/></svg>',
    "grid":       '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>',
    "sparkles":   '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3z"/></svg>',
    "store":      '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m2 7 4.41-4.41A2 2 0 0 1 7.83 2h8.34a2 2 0 0 1 1.42.59L22 7"/><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><path d="M15 22v-4a2 2 0 0 0-2-2h-2a2 2 0 0 0-2 2v4"/><path d="M2 7h20"/><path d="M22 7v3a2 2 0 0 1-2 2a2.7 2.7 0 0 1-1.59-.63.7.7 0 0 0-.82 0A2.7 2.7 0 0 1 16 12a2.7 2.7 0 0 1-1.59-.63.7.7 0 0 0-.82 0A2.7 2.7 0 0 1 12 12a2.7 2.7 0 0 1-1.59-.63.7.7 0 0 0-.82 0A2.7 2.7 0 0 1 8 12a2.7 2.7 0 0 1-1.59-.63.7.7 0 0 0-.82 0A2.7 2.7 0 0 1 4 12a2 2 0 0 1-2-2V7"/></svg>',
    "cart":       '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/></svg>',
    "creditcard": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>',
    "mail":       '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>',
    "userplus":   '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="19" y1="8" x2="19" y2="14"/><line x1="22" y1="11" x2="16" y2="11"/></svg>',
    "settings":   '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
    "users":      '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
}

_GROUP_LABELS = {
    "ai":   "Inteligência Artificial",
    "main": "Principal",
    "shop": "Loja & Pedidos",
    "mgmt": "Gestão",
}

_ROLES_POR_GRUPO = {
    "ai":   {"super_admin", "admin", "b2b", "b2c", "demo"},
    "main": {"super_admin", "admin", "b2b", "b2c", "demo"},
    "shop": {"super_admin", "admin", "b2b", "b2c"},
    "mgmt": {"super_admin", "admin"},
}

_ROLES_POR_PAGE = {
    "10_Usuarios": {"super_admin"},
}


def sidebar_logo() -> None:
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
            <span style="color:rgba(185,131,255,.5);font-size:.58rem;">\u2022 {fonte}</span>
          </div>
        </div>
      </div>
    </div>
    """)


def sidebar_section_label(label: str) -> None:
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
    st.sidebar.html("""
    <div style="
      margin:8px 16px;
      height:1px;
      background:linear-gradient(90deg,transparent,rgba(185,131,255,.25),transparent);
    "></div>
    """)


def sidebar_nav_highlight() -> None:
    st.sidebar.html("""
    <style>
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
    }
    [data-testid="stSidebarNavLink"]:hover {
      color: #fff !important;
      background: rgba(185,131,255,.14) !important;
      border-color: rgba(185,131,255,.28) !important;
    }
    [data-testid="stSidebarNavLink"][aria-current="page"] {
      color: #fff !important;
      background: rgba(124,58,237,.28) !important;
      border-color: rgba(185,131,255,.45) !important;
      font-weight: 600 !important;
    }
    [data-testid="stSidebarNavItems"] {
      padding: 4px 0 8px !important;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {
      color: rgba(255,255,255,.75) !important;
    }
    section[data-testid="stSidebar"] strong { color: #fff !important; }
    </style>
    """)


def sidebar_logout_button() -> None:
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
    }
    </style>
    <div id="hip-logout-btn-wrap">
      <a id="hip-logout-btn" href="?logout=1"
         onclick="window.parent.location.href='?logout=1'; return false;">
        🚶 Sair
      </a>
    </div>
    """)


def build_sidebar(
    show_cart: bool = True,
    cart_count: int = 0,
    cart_total: float = 0.0,
) -> None:
    """
    Sidebar Pro 2026 — com nav manual agrupado, IA primeiro, ícones SVG.
    Esconde o nav nativo do Streamlit e usa links HTML puros.
    """
    perfil = st.session_state.get("perfil", "demo")

    # ── CSS global do sidebar ──────────────────────────────────────────
    st.sidebar.html("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Syne:wght@700;800&display=swap');

    /* ── Oculta nav nativo do Streamlit ──────── */
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarNavSeparator"],
    [data-testid="stSidebarNavItems"] { display: none !important; }

    /* ── Background do sidebar: mesh dark ────── */
    section[data-testid="stSidebar"] > div {
      background:
        radial-gradient(ellipse at 10% 10%, rgba(124,58,237,.18) 0%, transparent 55%),
        radial-gradient(ellipse at 90% 85%, rgba(0,245,255,.06) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 50%, rgba(185,131,255,.04) 0%, transparent 70%),
        linear-gradient(180deg, #0a0015 0%, #110028 50%, #0a0015 100%) !important;
      background-attachment: fixed !important;
    }

    /* ── Logo ───────────────────────────── */
    .sb-logo {
      display: flex; align-items: center; gap: 11px;
      padding: 22px 18px 16px;
    }
    .sb-logo-icon {
      width: 38px; height: 38px; border-radius: 11px; flex-shrink: 0;
      background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%);
      display: flex; align-items: center; justify-content: center;
      font-family: 'Syne', sans-serif; font-weight: 800; font-size: 1.15rem;
      color: #fff; letter-spacing: -1px;
      box-shadow: 0 0 18px rgba(124,58,237,.55), 0 0 40px rgba(185,131,255,.12);
    }
    .sb-logo-name {
      font-family: 'Syne', sans-serif; font-weight: 800; font-size: .95rem;
      background: linear-gradient(90deg,#fff 20%,#b983ff 100%);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      background-clip: text; letter-spacing: .5px; line-height: 1.1;
    }
    .sb-logo-sub {
      font-family: 'Inter', sans-serif; font-size: .55rem;
      color: rgba(185,131,255,.5); letter-spacing: 3px;
      text-transform: uppercase; margin-top: 2px;
    }
    .sb-logo-divider {
      height: 1px;
      background: linear-gradient(90deg, transparent, rgba(185,131,255,.3), transparent);
      margin: 0 18px 8px;
    }

    /* ── Grupo label ─────────────────────── */
    .sb-group {
      font-family: 'Inter', sans-serif; font-size: .58rem; font-weight: 700;
      letter-spacing: 1.8px; text-transform: uppercase;
      color: rgba(185,131,255,.4);
      padding: 14px 18px 5px;
    }

    /* ── Item do menu ───────────────────── */
    .sb-item {
      display: flex; align-items: center; gap: 10px;
      padding: 8px 14px; margin: 1px 8px;
      border-radius: 10px;
      font-family: 'Inter', sans-serif; font-size: .86rem; font-weight: 500;
      color: rgba(255,255,255,.72);
      text-decoration: none;
      border: 1px solid transparent;
      transition: all .18s cubic-bezier(.4,0,.2,1);
      cursor: pointer;
    }
    .sb-item:hover {
      color: #fff;
      background: rgba(185,131,255,.1);
      border-color: rgba(185,131,255,.22);
      text-decoration: none;
    }
    .sb-item.active {
      color: #fff;
      background: linear-gradient(135deg, rgba(124,58,237,.3) 0%, rgba(185,131,255,.12) 100%);
      border-color: rgba(185,131,255,.4);
      font-weight: 600;
      box-shadow: 0 0 12px rgba(185,131,255,.12), inset 0 0 0 1px rgba(185,131,255,.08);
    }
    .sb-item.ai-item {
      background: linear-gradient(135deg, rgba(0,245,255,.06) 0%, rgba(124,58,237,.12) 100%);
      border-color: rgba(0,245,255,.18);
      color: rgba(200,255,255,.85);
    }
    .sb-item.ai-item:hover {
      background: linear-gradient(135deg, rgba(0,245,255,.14) 0%, rgba(124,58,237,.22) 100%);
      border-color: rgba(0,245,255,.38);
      box-shadow: 0 0 16px rgba(0,245,255,.14);
      color: #fff;
    }
    .sb-item.ai-item.active {
      background: linear-gradient(135deg, rgba(0,245,255,.18) 0%, rgba(124,58,237,.3) 100%);
      border-color: rgba(0,245,255,.5);
      box-shadow: 0 0 20px rgba(0,245,255,.18), 0 0 40px rgba(124,58,237,.1);
      color: #fff;
    }
    .sb-icon { flex-shrink: 0; opacity: .8; }
    .sb-item:hover .sb-icon, .sb-item.active .sb-icon { opacity: 1; }

    /* ── Badge (cart count) ──────────────── */
    .sb-badge {
      margin-left: auto;
      background: linear-gradient(135deg, #7c3aed, #b983ff);
      color: #fff; font-size: .58rem; font-weight: 700;
      padding: 2px 7px; border-radius: 999px;
      min-width: 18px; text-align: center;
    }

    /* ── Usuário card ──────────────────── */
    .sb-user {
      display: flex; align-items: center; gap: 10px;
      padding: 10px 12px; margin: 8px;
      background: linear-gradient(135deg,rgba(124,58,237,.18),rgba(185,131,255,.07));
      border: 1px solid rgba(185,131,255,.25);
      border-radius: 14px;
    }
    .sb-user-avatar {
      width: 40px; height: 40px; border-radius: 50%; flex-shrink: 0;
      background: linear-gradient(135deg,rgba(124,58,237,.5),rgba(185,131,255,.25));
      border: 1.5px solid rgba(185,131,255,.4);
      display: flex; align-items: center; justify-content: center;
      font-size: 1.1rem;
    }
    .sb-user-name {
      font-family: 'Inter', sans-serif; font-weight: 700; font-size: .84rem;
      color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
      max-width: 130px;
    }
    .sb-user-role {
      display: inline-block;
      background: linear-gradient(135deg,rgba(124,58,237,.6),rgba(91,33,182,.8));
      color: #e9d5ff; font-size: .56rem; font-weight: 700;
      letter-spacing: .8px; padding: 2px 8px; border-radius: 999px;
      text-transform: uppercase; margin-top: 4px;
    }

    /* ── Divider ───────────────────────── */
    .sb-divider {
      height: 1px; margin: 4px 18px;
      background: linear-gradient(90deg,transparent,rgba(185,131,255,.2),transparent);
    }

    /* ── Botão Sair fixo no rodapé ───────── */
    #sb-logout {
      position: fixed; bottom: 0; left: 0; width: 244px;
      padding: 12px 14px 18px;
      background: linear-gradient(0deg, #0a0015 80%, transparent);
      z-index: 9999;
    }
    #sb-logout a {
      display: flex; align-items: center; justify-content: center; gap: 8px;
      width: 100%; padding: 10px 0;
      background: rgba(255,255,255,.05);
      color: rgba(255,255,255,.75);
      border: 1px solid rgba(185,131,255,.2);
      border-radius: 11px;
      font-family: 'Inter', sans-serif; font-size: .84rem; font-weight: 600;
      text-decoration: none; letter-spacing: .01em;
      transition: all .18s ease;
    }
    #sb-logout a:hover {
      background: rgba(185,131,255,.16);
      color: #fff;
      border-color: rgba(185,131,255,.45);
    }
    </style>
    """)

    # ── Logo ─────────────────────────────────────────────────────
    st.sidebar.html("""
    <div class="sb-logo">
      <div class="sb-logo-icon">H</div>
      <div>
        <div class="sb-logo-name">HIPNUS</div>
        <div class="sb-logo-sub">Cosm&eacute;ticos</div>
      </div>
    </div>
    <div class="sb-logo-divider"></div>
    """)

    # ── Card do usuário ───────────────────────────────────────
    nome        = st.session_state.get("nome", "Visitante")
    display_nm  = st.session_state.get("display_name", "") or nome
    role_label  = perfil.replace("_", " ").upper()
    icones_role = {"super_admin": "⭐", "admin": "🛡️", "b2b": "🎤", "b2c": "👤", "demo": "👀"}
    icone       = icones_role.get(perfil, "👤")

    st.sidebar.html(f"""
    <div class="sb-user">
      <div class="sb-user-avatar">{icone}</div>
      <div style="min-width:0;">
        <div class="sb-user-name" title="{display_nm}">{display_nm}</div>
        <div class="sb-user-role">{role_label}</div>
      </div>
    </div>
    """)

    # ── Nav agrupado ───────────────────────────────────────────
    last_group = None
    cart_count_local = cart_count

    for grupo, page_key, label, icon_key in _NAV_ITEMS:
        # verifica permissão
        if perfil not in _ROLES_POR_GRUPO.get(grupo, set()):
            continue
        if perfil not in _ROLES_POR_PAGE.get(page_key, {perfil}):
            continue

        # label do grupo
        if grupo != last_group:
            group_html = f'<div class="sb-group">{_GROUP_LABELS.get(grupo, grupo)}</div>'
            if last_group is not None:
                group_html = '<div class="sb-divider"></div>' + group_html
            st.sidebar.html(group_html)
            last_group = grupo

        icon_svg  = _ICONS.get(icon_key, "")
        href      = f"/{page_key}"
        ai_cls    = " ai-item" if grupo == "ai" else ""
        badge_html = ""
        if page_key == "5_Carrinho" and cart_count_local > 0:
            badge_html = f'<span class="sb-badge">{cart_count_local}</span>'

        item_html = f"""
        <a class="sb-item{ai_cls}" href="{href}">
          <span class="sb-icon">{icon_svg}</span>
          <span>{label}</span>
          {badge_html}
        </a>"""
        st.sidebar.html(item_html)

    # ── Botão Sair ────────────────────────────────────────────
    st.sidebar.html("""
    <div id="sb-logout">
      <a href="?logout=1" onclick="window.parent.location.href='?logout=1'; return false;">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
          <polyline points="16 17 21 12 16 7"/>
          <line x1="21" y1="12" x2="9" y2="12"/>
        </svg>
        Sair da plataforma
      </a>
    </div>
    <div style="height:64px;"></div>
    """)
