"""
auth.py — HIPNUS COSMÉTICOS
==============================
Guarda de autenticação + Sidebar Pro Redesign 2026.
Nav usa st.sidebar.page_link() para navegação real no Streamlit.
"""
from __future__ import annotations

import streamlit as st

ROLES_PRIVILEGIADOS = {"super_admin", "admin"}
ROLES_PROFISSIONAIS = {"super_admin", "admin", "b2b"}

LOGIN_PAGE  = "streamlit_app.py"
HOME_PAGE   = "pages/0_🏠_Home.py"
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
# Usa st.sidebar.page_link() para navegação real + CSS injetado via
# st.sidebar.html() para estilizar os botões nativos do Streamlit.
# ───────────────────────────────────────────────────────────────────────

# (grupo, page_path_relativo, label, ícone_emoji)
# page_path deve ser relativo à raiz do app (onde fica o streamlit_app.py)
_NAV_ITEMS = [
    # IA PRIMEIRO
    ("ai",   "pages/10_🤖_IA_Consultora.py",     "🤖  IA Consultora",      {"super_admin","admin","b2b","b2c","demo"}),
    # Principal
    ("main", "pages/0_🏠_Home.py",               "🏠  Home",               {"super_admin","admin","b2b","b2c","demo"}),
    ("main", "pages/0_📊_Dashboard.py",           "📊  Dashboard",          {"super_admin","admin","b2b","b2c","demo"}),
    # Loja
    ("shop", "pages/1_🛍️_Catálogo.py",           "🛍️  Catálogo",           {"super_admin","admin","b2b","b2c"}),
    ("shop", "pages/2_✨_Linhas.py",              "✨  Linhas",             {"super_admin","admin","b2b","b2c"}),
    ("shop", "pages/3_🏪_Loja_do_Parceiro.py",   "🏪  Loja Parceiro",      {"super_admin","admin","b2b"}),
    ("shop", "pages/4_🛒_Carrinho.py",            "🛒  Carrinho",           {"super_admin","admin","b2b","b2c"}),
    ("shop", "pages/5_💳_Checkout.py",            "💳  Checkout",           {"super_admin","admin","b2b","b2c"}),
    # Gestão
    ("mgmt", "pages/6_Convites.py",               "✉️  Convites",           {"super_admin","admin"}),
    ("mgmt", "pages/7_Cadastro_Parceiro.py",      "➕  Cadastro Parceiro",  {"super_admin","admin"}),
    ("mgmt", "pages/8_Configuracao.py",           "⚙️  Configurações",      {"super_admin","admin"}),
    ("mgmt", "pages/9_👥_Usuarios.py",            "👥  Usuários",           {"super_admin"}),
]

_GROUP_LABELS = {
    "ai":   "✦ Inteligência Artificial",
    "main": "Principal",
    "shop": "Loja & Pedidos",
    "mgmt": "Gestão",
}


def _inject_sidebar_css() -> None:
    """Injeta CSS premium para estilizar os page_link nativos do Streamlit."""
    st.sidebar.html("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Syne:wght@700;800&display=swap');

    /* ── Fundo sidebar mesh dark ──────────────────────────────── */
    section[data-testid="stSidebar"] > div {
      background:
        radial-gradient(ellipse at 10% 10%, rgba(124,58,237,.2) 0%, transparent 55%),
        radial-gradient(ellipse at 90% 85%, rgba(0,245,255,.07) 0%, transparent 50%),
        linear-gradient(180deg, #0a0015 0%, #110028 55%, #0a0015 100%) !important;
    }

    /* ── Oculta nav automático do Streamlit ───────────────────── */
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarNavSeparator"],
    [data-testid="stSidebarNavItems"] { display: none !important; }

    /* ── page_link base ───────────────────────────────────────── */
    section[data-testid="stSidebar"] [data-testid="stPageLink"] a,
    section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {
      display: flex !important;
      align-items: center !important;
      gap: 8px !important;
      padding: 9px 14px !important;
      margin: 1px 6px !important;
      border-radius: 10px !important;
      border: 1px solid transparent !important;
      font-family: 'Inter', sans-serif !important;
      font-size: .86rem !important;
      font-weight: 500 !important;
      color: rgba(255,255,255,.78) !important;
      text-decoration: none !important;
      transition: all .18s ease !important;
      background: transparent !important;
    }
    section[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover,
    section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {
      color: #fff !important;
      background: rgba(185,131,255,.12) !important;
      border-color: rgba(185,131,255,.25) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"],
    section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] {
      color: #fff !important;
      background: linear-gradient(135deg, rgba(124,58,237,.32), rgba(185,131,255,.14)) !important;
      border-color: rgba(185,131,255,.45) !important;
      font-weight: 600 !important;
      box-shadow: 0 0 14px rgba(185,131,255,.15) !important;
    }

    /* ── Botão Sair nativo sidebar ────────────────────────────── */
    section[data-testid="stSidebar"] div.block-container div.stButton > button {
      width: 100% !important;
      background: rgba(255,255,255,.05) !important;
      color: rgba(255,255,255,.78) !important;
      border: 1px solid rgba(185,131,255,.22) !important;
      border-radius: 11px !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 600 !important;
      font-size: .86rem !important;
      padding: 10px 0 !important;
      min-height: 42px !important;
      transition: all .18s ease !important;
      margin-top: 4px !important;
    }
    section[data-testid="stSidebar"] div.block-container div.stButton > button:hover {
      background: rgba(185,131,255,.18) !important;
      color: #fff !important;
      border-color: rgba(185,131,255,.5) !important;
    }

    /* ── Textos genéricos sidebar ─────────────────────────────── */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] div { color: rgba(255,255,255,.75); }
    section[data-testid="stSidebar"] strong { color: #fff; }

    /* ── Scrollbar slim ───────────────────────────────────────── */
    section[data-testid="stSidebar"] ::-webkit-scrollbar { width: 4px; }
    section[data-testid="stSidebar"] ::-webkit-scrollbar-track { background: transparent; }
    section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
      background: rgba(124,58,237,.5); border-radius: 4px;
    }
    </style>
    """)


def build_sidebar(
    show_cart: bool = True,
    cart_count: int = 0,
    cart_total: float = 0.0,
) -> None:
    """
    Sidebar Pro 2026.
    Usa st.sidebar.page_link() (API nativa) para navegação funcional.
    CSS premium injetado via st.sidebar.html().
    """
    perfil = st.session_state.get("perfil", "demo")

    # 1. CSS premium
    _inject_sidebar_css()

    # 2. Logo
    st.sidebar.html("""
    <div style="
      display:flex;align-items:center;gap:11px;
      padding:20px 16px 14px;
    ">
      <div style="
        width:38px;height:38px;border-radius:11px;flex-shrink:0;
        background:linear-gradient(135deg,#7c3aed,#5b21b6);
        display:flex;align-items:center;justify-content:center;
        font-family:'Syne',sans-serif;font-weight:800;font-size:1.1rem;
        color:#fff;
        box-shadow:0 0 18px rgba(124,58,237,.6),0 0 40px rgba(185,131,255,.15);
      ">H</div>
      <div>
        <div style="
          font-family:'Syne',sans-serif;font-weight:800;font-size:.95rem;
          background:linear-gradient(90deg,#fff 20%,#b983ff 100%);
          -webkit-background-clip:text;-webkit-text-fill-color:transparent;
          background-clip:text;letter-spacing:.4px;line-height:1.1;
        ">HIPNUS</div>
        <div style="
          font-family:'Inter',sans-serif;font-size:.53rem;
          color:rgba(185,131,255,.5);letter-spacing:3px;
          text-transform:uppercase;margin-top:2px;
        ">Cosm&eacute;ticos</div>
      </div>
    </div>
    <div style="height:1px;margin:0 16px 8px;
      background:linear-gradient(90deg,transparent,rgba(185,131,255,.3),transparent);
    "></div>
    """)

    # 3. Card usuário
    nome       = st.session_state.get("nome", "Visitante")
    display_nm = st.session_state.get("display_name", "") or nome
    role_label = perfil.replace("_", " ").upper()
    icone_map  = {"super_admin": "⭐", "admin": "🛡️", "b2b": "🎤", "b2c": "👤", "demo": "👀"}
    icone      = icone_map.get(perfil, "👤")

    st.sidebar.html(f"""
    <div style="
      display:flex;align-items:center;gap:10px;
      padding:10px 12px;margin:0 8px 4px;
      background:linear-gradient(135deg,rgba(124,58,237,.2),rgba(185,131,255,.07));
      border:1px solid rgba(185,131,255,.28);border-radius:14px;
    ">
      <div style="
        width:38px;height:38px;border-radius:50%;flex-shrink:0;
        background:linear-gradient(135deg,rgba(124,58,237,.5),rgba(185,131,255,.2));
        border:1.5px solid rgba(185,131,255,.4);
        display:flex;align-items:center;justify-content:center;font-size:1rem;
      ">{icone}</div>
      <div style="min-width:0;">
        <div style="
          font-family:'Inter',sans-serif;font-weight:700;font-size:.84rem;
          color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
          max-width:130px;line-height:1.3;
        " title="{display_nm}">{display_nm}</div>
        <div style="
          display:inline-block;margin-top:4px;
          background:linear-gradient(135deg,rgba(124,58,237,.6),rgba(91,33,182,.8));
          color:#e9d5ff;font-size:.56rem;font-weight:700;
          letter-spacing:.8px;padding:2px 9px;border-radius:999px;
          text-transform:uppercase;
        ">{role_label}</div>
      </div>
    </div>
    """)

    # 4. Nav com page_link agrupado
    last_group = None

    for grupo, page_path, label, roles_ok in _NAV_ITEMS:
        if perfil not in roles_ok:
            continue

        # label do grupo
        if grupo != last_group:
            if last_group is not None:
                st.sidebar.html("""
                <div style="height:1px;margin:6px 16px;
                  background:linear-gradient(90deg,transparent,rgba(185,131,255,.18),transparent);
                "></div>""")
            g_label = _GROUP_LABELS.get(grupo, grupo)
            st.sidebar.html(f"""
            <div style="
              font-family:'Inter',sans-serif;font-size:.58rem;font-weight:700;
              letter-spacing:1.8px;text-transform:uppercase;
              color:rgba(185,131,255,.42);padding:12px 18px 4px;
            ">{g_label}</div>""")
            last_group = grupo

        # badge carrinho
        if "Carrinho" in label and cart_count > 0:
            label = f"{label}  ({cart_count})"

        try:
            st.sidebar.page_link(page_path, label=label)
        except Exception:
            pass  # página pode não existir em alguns deploys

    # 5. Botão Sair
    st.sidebar.html("""<div style="height:12px;"></div>""")
    with st.sidebar:
        if st.button("🚪  Sair da plataforma", key="sb_logout_btn", use_container_width=True):
            logout()
