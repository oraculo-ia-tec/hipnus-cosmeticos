"""
auth.py — HIPNUS COSMÉTICOS
==============================
Guarda de autenticação + Sidebar Pro Redesign 2026.

Fix 2026-06-29 v2: persistência definitiva de imagens.
  - Avatar do usuário: recarregado do banco a cada page-load quando ausente
    na sessão (sem depender de flag _avatar_loaded que bloqueava a recarga).
  - Foto da Chiara: recarregada do banco a cada page-load quando ausente
    na sessão (sem depender de flag _chiara_loaded que bloqueava a recarga).
  - Resultado: imagens sobrevivem a logout/login e reinicialização.
"""
from __future__ import annotations

from pathlib import Path
import streamlit as st

ROLES_PRIVILEGIADOS = {"super_admin", "admin"}
ROLES_PROFISSIONAIS = {"super_admin", "admin", "b2b"}

LOGIN_PAGE  = "streamlit_app.py"
HOME_PAGE   = "pages/1_Home.py"
_LOGIN_PAGE = LOGIN_PAGE
_HOME_PAGE  = HOME_PAGE

DEBUG_SIDEBAR = False


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


def _normalize_role(role: str | None) -> str:
    role = (role or "demo").strip().lower()
    aliases = {
        "super user":  "super_admin",
        "superuser":   "super_admin",
        "super-admin": "super_admin",
        "super admin": "super_admin",
        "superadmin":  "super_admin",
        "admin":       "admin",
        "b2b":         "b2b",
        "b2c":         "b2c",
        "demo":        "demo",
    }
    return aliases.get(role, role)


def _carregar_chiara_no_session() -> None:
    """
    Carrega nome, cargo e foto da Chiara do banco para o session_state.

    Estratégia sem flag bloqueante:
      - Sempre verifica se chiara_foto_b64 está presente na sessão.
      - Se não estiver, consulta o banco e preenche todos os campos.
      - Isso garante que a foto da Chiara reaparece após logout/login
        sem precisar resetar manualmente nenhuma flag.
    """
    # Se a foto já está na sessão, não precisa ir ao banco
    if st.session_state.get("chiara_foto_b64"):
        return
    try:
        import sys
        _root = Path(__file__).resolve().parents[2]
        if str(_root) not in sys.path:
            sys.path.insert(0, str(_root))
        from lib.user_db import carregar_config_chiara
        cfg = carregar_config_chiara()
        if cfg.get("nome"):
            st.session_state["chiara_nome"]      = cfg["nome"]
        if cfg.get("cargo"):
            st.session_state["chiara_cargo"]     = cfg["cargo"]
        if cfg.get("foto_b64"):
            st.session_state["chiara_foto_b64"]  = cfg["foto_b64"]
            st.session_state["chiara_foto_mime"] = cfg.get("foto_mime", "image/jpeg")
        if cfg.get("saudacao"):
            st.session_state["chiara_saudacao"]  = cfg["saudacao"]
    except Exception:
        pass


def _restaurar_avatar_usuario(email: str) -> None:
    """
    Recarrega avatar_b64 do parceiro no banco quando ausente na sessão.

    Estratégia sem flag bloqueante:
      - Sempre verifica se avatar_b64 está presente na sessão.
      - Se não estiver E houver e-mail, consulta o banco.
      - Isso garante que o avatar reaparece após logout/login para
        TODOS os usuários cadastrados no banco (incluindo parceiros
        que fizeram upload de foto em sessões anteriores).
    """
    # Se já tem avatar na sessão, não precisa ir ao banco
    if st.session_state.get("avatar_b64"):
        return
    if not email:
        return
    try:
        import sys
        _root = Path(__file__).resolve().parents[2]
        if str(_root) not in sys.path:
            sys.path.insert(0, str(_root))
        from lib.user_db import buscar_por_email
        parceiro = buscar_por_email(email)
        if parceiro and parceiro.get("avatar_b64"):
            st.session_state["avatar_b64"] = parceiro["avatar_b64"]
    except Exception:
        pass


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
        "perfil":            _normalize_role(role),
        "display_name":      display_name,
        "email":             email,
        "token":             token,
        "via_api":           via_api,
        "avatar_b64":        avatar_b64,   # None se não vier do banco; _restaurar cobre depois
        "session_start":     time.time(),
        "_jwt_dialog_shown": False,
        # Limpa caches de foto para forçar recarga nas funções acima
        "chiara_foto_b64":   None,
        "chiara_foto_mime":  None,
        "chiara_nome":       None,
        "chiara_cargo":      None,
        "chiara_saudacao":   None,
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
            # Tenta buscar avatar no banco para usuários demo que também
            # estão cadastrados como parceiros (ex: william tem e-mail real)
            avatar_b64 = None
            try:
                import sys
                _root = Path(__file__).resolve().parents[2]
                if str(_root) not in sys.path:
                    sys.path.insert(0, str(_root))
                from lib.user_db import buscar_por_email
                p = buscar_por_email(u["email"])
                if p:
                    avatar_b64 = p.get("avatar_b64")
            except Exception:
                pass
            _gravar_sessao(
                nome=u["nome"], username=uname, role=u["role"],
                display_name=u["display_name"], email=u["email"],
                token=None, via_api=False, avatar_b64=avatar_b64,
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

    # ── Restaura fotos a cada page-load (sem flag bloqueante) ────────
    # As funções abaixo verificam internamente se já há valor na sessão
    # e só consultam o banco quando necessário — sem custo extra.
    email = st.session_state.get("email", "")
    _restaurar_avatar_usuario(email)
    _carregar_chiara_no_session()

    usuario = {
        "login":        st.session_state.get("usuario", ""),
        "perfil":       _normalize_role(st.session_state.get("perfil", "demo")),
        "nome":         st.session_state.get("nome",    "Visitante"),
        "display_name": st.session_state.get("display_name", ""),
        "email":        st.session_state.get("email",   ""),
        "token":        st.session_state.get("token",   None),
        "via_api":      st.session_state.get("via_api", False),
        "avatar_b64":   st.session_state.get("avatar_b64", None),
    }
    st.session_state["perfil"] = usuario["perfil"]
    if perfis_permitidos and usuario["perfil"] not in perfis_permitidos:
        st.error("🚫 Você não tem permissão para acessar esta página.")
        st.stop()
    return usuario


def logout() -> None:
    for key in [
        "autenticado", "usuario", "perfil", "nome",
        "display_name", "email", "token", "via_api", "avatar_b64",
        "session_start", "_jwt_dialog_shown",
        "_chiara_loaded", "_avatar_loaded",
        "chiara_nome", "chiara_cargo", "chiara_foto_b64",
        "chiara_foto_mime", "chiara_foto_hash", "chiara_saudacao",
    ]:
        st.session_state.pop(key, None)
    st.query_params.clear()
    st.switch_page(_LOGIN_PAGE)


# ───────────────────────────────────────────────────────────────────────
# SIDEBAR PRO REDESIGN 2026
# ───────────────────────────────────────────────────────────────────────

_NAV_ITEMS = [
    ("pages/11_IA_Consultora.py",      "🤖  IA Consultora",     {"super_admin","admin","b2b","b2c","demo"}),
    ("pages/1_Home.py",                "🏠  Home",              {"super_admin","admin","b2b","b2c","demo"}),
    ("pages/0_Dashboard.py",           "📊  Dashboard",         {"super_admin","admin","b2b","b2c","demo"}),
    ("pages/2_Catalogo.py",            "🛍️  Catálogo",          {"super_admin","admin","b2b","b2c"}),
    ("pages/3_Linhas.py",              "✨  Linhas",            {"super_admin","admin","b2b","b2c"}),
    ("pages/4_Loja_Parceiro.py",       "🏪  Loja Parceiro",     {"super_admin","admin","b2b"}),
    ("pages/5_Carrinho.py",            "🛒  Carrinho",          {"super_admin","admin","b2b","b2c"}),
    ("pages/6_Checkout.py",            "💳  Checkout",          {"super_admin","admin","b2b","b2c"}),
    ("pages/7_Convites.py",            "✉️  Convites",          {"super_admin","admin"}),
    ("pages/8_Cadastro_Parceiro.py",   "➕  Cadastro Parceiro", {"super_admin","admin"}),
    ("pages/9_Configuracao.py",        "⚙️  Configurações",     {"super_admin","admin"}),
    ("pages/10_Usuarios.py",           "👥  Usuários",          {"super_admin"}),
]


def _page_exists(page_path: str) -> bool:
    try:
        candidates = [
            Path.cwd() / page_path,
            Path(__file__).resolve().parents[2] / page_path,
            Path(__file__).resolve().parents[1] / page_path,
        ]
        return any(p.exists() for p in candidates)
    except Exception:
        return False


def _debug_sidebar_state(perfil: str) -> None:
    if not DEBUG_SIDEBAR:
        return
    with st.sidebar.expander("🧪 Debug Sidebar", expanded=False):
        st.write("**perfil_raw:**", st.session_state.get("perfil"))
        st.write("**perfil_normalizado:**", perfil)
        st.write("**autenticado:**", st.session_state.get("autenticado"))
        st.write("**usuario:**", st.session_state.get("usuario"))
        st.write("**cwd:**", str(Path.cwd()))
        rows = []
        for page_path, label, roles_ok in _NAV_ITEMS:
            rows.append({
                "label":          label,
                "page_path":      page_path,
                "existe_arquivo": _page_exists(page_path),
                "permitido":      perfil in roles_ok,
                "roles_ok":       ", ".join(sorted(roles_ok)),
            })
        st.dataframe(rows, use_container_width=True)
        if st.checkbox("Ver session_state completo", key="dbg_ss_full"):
            st.json(dict(st.session_state))


_SAIR_CSS = """
<style>
/* HIPNUS — Botão SAIR na sidebar */
section[data-testid="stSidebar"] div[data-testid="stButton"] > button,
section[data-testid="stSidebar"] div[data-testid="stButton"] > button > div,
section[data-testid="stSidebar"] div[data-testid="stButton"] > button p {
    background-color: rgba(185, 28, 28, 0.25) !important;
    background-image: none !important;
    color: #fca5a5 !important;
    border: 1.5px solid rgba(239, 68, 68, 0.45) !important;
    border-radius: 11px !important;
    font-weight: 700 !important;
    font-size: 0.86rem !important;
    min-height: 44px !important;
    transition: all 0.18s ease !important;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover,
section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover > div,
section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover p {
    background-color: rgba(220, 38, 38, 0.40) !important;
    color: #ffffff !important;
    border-color: rgba(239, 68, 68, 0.75) !important;
    box-shadow: 0 0 20px rgba(239, 68, 68, 0.30) !important;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] > button:active,
section[data-testid="stSidebar"] div[data-testid="stButton"] > button:focus,
section[data-testid="stSidebar"] div[data-testid="stButton"] > button:active > div,
section[data-testid="stSidebar"] div[data-testid="stButton"] > button:focus > div,
section[data-testid="stSidebar"] div[data-testid="stButton"] > button:active p,
section[data-testid="stSidebar"] div[data-testid="stButton"] > button:focus p {
    background-color: rgba(220, 38, 38, 0.50) !important;
    color: #ffffff !important;
    outline: none !important;
    box-shadow: none !important;
}
</style>
"""


def _inject_sidebar_css() -> None:
    st.markdown(_SAIR_CSS, unsafe_allow_html=True)
    st.sidebar.html("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Syne:wght@700;800&display=swap');

    section[data-testid="stSidebar"] > div {
      background:
        radial-gradient(ellipse at 10% 10%, rgba(124,58,237,.2) 0%, transparent 55%),
        radial-gradient(ellipse at 90% 85%, rgba(0,245,255,.07) 0%, transparent 50%),
        linear-gradient(180deg, #0a0015 0%, #110028 55%, #0a0015 100%) !important;
    }
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarNavSeparator"],
    [data-testid="stSidebarNavItems"] { display: none !important; }

    section[data-testid="stSidebar"] [data-testid="stPageLink"] a,
    section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {
      display: flex !important; align-items: center !important; gap: 8px !important;
      padding: 9px 14px !important; margin: 1px 6px !important;
      border-radius: 10px !important; border: 1px solid transparent !important;
      font-family: 'Inter', sans-serif !important; font-size: .86rem !important;
      font-weight: 500 !important; color: rgba(255,255,255,.78) !important;
      text-decoration: none !important; transition: all .18s ease !important;
      background: transparent !important;
    }
    section[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover,
    section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {
      color: #fff !important; background: rgba(185,131,255,.12) !important;
      border-color: rgba(185,131,255,.25) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"],
    section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] {
      color: #fff !important;
      background: linear-gradient(135deg, rgba(124,58,237,.32), rgba(185,131,255,.14)) !important;
      border-color: rgba(185,131,255,.45) !important;
      font-weight: 600 !important; box-shadow: 0 0 14px rgba(185,131,255,.15) !important;
    }
    .hip-sidebar-divider {
      height: 1px; margin: 14px 16px 10px;
      background: linear-gradient(90deg, transparent, rgba(185,131,255,.45), rgba(0,245,255,.15), transparent);
      border: none;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label { color: rgba(255,255,255,.75); }
    section[data-testid="stSidebar"] strong { color: #fff; }
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
    """Sidebar Pro 2026 — menu completo, persistente em todas as páginas."""
    perfil = _normalize_role(st.session_state.get("perfil", "demo"))
    st.session_state["perfil"] = perfil

    _inject_sidebar_css()
    _debug_sidebar_state(perfil)

    # Logo
    st.sidebar.html("""
    <div style="display:flex;align-items:center;gap:11px;padding:20px 16px 14px;">
      <div style="width:38px;height:38px;border-radius:11px;flex-shrink:0;
        background:linear-gradient(135deg,#7c3aed,#5b21b6);
        display:flex;align-items:center;justify-content:center;
        font-family:'Syne',sans-serif;font-weight:800;font-size:1.1rem;color:#fff;
        box-shadow:0 0 18px rgba(124,58,237,.6),0 0 40px rgba(185,131,255,.15);">H</div>
      <div>
        <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:.95rem;
          background:linear-gradient(90deg,#fff 20%,#b983ff 100%);
          -webkit-background-clip:text;-webkit-text-fill-color:transparent;
          background-clip:text;letter-spacing:.4px;line-height:1.1;">HIPNUS</div>
        <div style="font-family:'Inter',sans-serif;font-size:.53rem;
          color:rgba(185,131,255,.5);letter-spacing:3px;
          text-transform:uppercase;margin-top:2px;">Cosm&eacute;ticos</div>
      </div>
    </div>
    <div style="height:1px;margin:0 16px 8px;
      background:linear-gradient(90deg,transparent,rgba(185,131,255,.3),transparent);"></div>
    """)

    # Card usuário
    nome       = st.session_state.get("nome", "Visitante")
    display_nm = st.session_state.get("display_name", "") or nome
    role_label = perfil.replace("_", " ").upper()
    icone      = {"super_admin":"⭐","admin":"🛡️","b2b":"🎤","b2c":"👤","demo":"👀"}.get(perfil, "👤")

    st.sidebar.html(f"""
    <div style="display:flex;align-items:center;gap:10px;
      padding:10px 12px;margin:0 8px 8px;
      background:linear-gradient(135deg,rgba(124,58,237,.2),rgba(185,131,255,.07));
      border:1px solid rgba(185,131,255,.28);border-radius:14px;">
      <div style="width:38px;height:38px;border-radius:50%;flex-shrink:0;
        background:linear-gradient(135deg,rgba(124,58,237,.5),rgba(185,131,255,.2));
        border:1.5px solid rgba(185,131,255,.4);
        display:flex;align-items:center;justify-content:center;font-size:1rem;">{icone}</div>
      <div style="min-width:0;">
        <div style="font-family:'Inter',sans-serif;font-weight:700;font-size:.84rem;
          color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
          max-width:130px;line-height:1.3;" title="{display_nm}">{display_nm}</div>
        <div style="display:inline-block;margin-top:4px;
          background:linear-gradient(135deg,rgba(124,58,237,.6),rgba(91,33,182,.8));
          color:#e9d5ff;font-size:.56rem;font-weight:700;
          letter-spacing:.8px;padding:2px 9px;border-radius:999px;
          text-transform:uppercase;">{role_label}</div>
      </div>
    </div>
    """)

    # Menus flat
    for page_path, label, roles_ok in _NAV_ITEMS:
        if perfil not in roles_ok:
            continue
        lbl = f"{label}  ({cart_count})" if "Carrinho" in label and cart_count > 0 else label
        try:
            st.sidebar.page_link(page_path, label=lbl)
        except Exception:
            pass

    # Divider + botão SAIR
    st.sidebar.html('<hr class="hip-sidebar-divider">')
    with st.sidebar:
        if st.button("🚨  SAIR", key="sb_logout_btn", use_container_width=True):
            logout()


# ─── Aliases de compatibilidade ──────────────────────────────────────
def sidebar_logo() -> None:
    _maybe_build_sidebar()

def sidebar_user_info() -> None:
    pass

def sidebar_logout_button() -> None:
    pass

def sidebar_nav_highlight() -> None:
    pass

def sidebar_section_label(label: str) -> None:
    pass

def sidebar_divider() -> None:
    pass

def _maybe_build_sidebar(
    show_cart: bool = True,
    cart_count: int = 0,
    cart_total: float = 0.0,
) -> None:
    run_id = id(st.session_state)
    key = f"_sb_done_{run_id}"
    if not st.session_state.get(key):
        st.session_state[key] = True
        build_sidebar(show_cart=show_cart, cart_count=cart_count, cart_total=cart_total)
