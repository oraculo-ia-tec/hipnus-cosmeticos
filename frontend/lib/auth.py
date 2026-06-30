"""
auth.py — HIPNUS COSMÉTICOS
==============================
v7 — 2026-06-29:
  - Fix layout item Chiara: usa <a href> nativo num único st.sidebar.html().
    Elimina o problema de imagem+texto misturados causado por dois elementos
    Streamlit separados (html + page_link).
  - Botão SAIR usa cor dinâmica do tema.
  - Sidebar responde ao tema ativo.
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
        "avatar_b64":        avatar_b64,
        "session_start":     time.time(),
        "_jwt_dialog_shown": False,
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
    ("pages/11_IA_Consultora.py",      "__chiara__",            {"super_admin","admin","b2b","b2c","demo"}),
    ("pages/1_Home.py",                "🏠  Home",              {"super_admin","admin","b2b","b2c","demo"}),
    ("pages/0_Dashboard.py",           "📊  Dashboard",         {"super_admin","admin","b2b","b2c","demo"}),
    ("pages/2_Catalogo.py",            "🛍️  Catálogo",          {"super_admin","admin","b2b","b2c"}),
    ("pages/3_Linhas.py",              "✨  Linhas",            {"super_admin","admin","b2b","b2c"}),
    ("pages/4_Loja_Parceiro.py",       "🏡  Loja Parceiro",     {"super_admin","admin","b2b"}),
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


def _hex_rgba(hex_color: str, alpha: float) -> str:
    """Utilitário global: converte hex + alpha em rgba()."""
    try:
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    except Exception:
        return f"rgba(124,58,237,{alpha})"


def _inject_sidebar_css() -> None:
    cor_primary = st.session_state.get("tema_primary", "#7c3aed")
    cor_accent  = st.session_state.get("tema_accent",  "#b983ff")

    p_20 = _hex_rgba(cor_primary, 0.20)
    p_32 = _hex_rgba(cor_primary, 0.32)
    p_50 = _hex_rgba(cor_primary, 0.50)
    a_12 = _hex_rgba(cor_accent,  0.12)
    a_15 = _hex_rgba(cor_accent,  0.15)
    a_25 = _hex_rgba(cor_accent,  0.25)
    a_45 = _hex_rgba(cor_accent,  0.45)

    sair_bg       = f"linear-gradient(135deg,{_hex_rgba(cor_primary,0.30)},{_hex_rgba(cor_primary,0.18)})"
    sair_border   = _hex_rgba(cor_accent, 0.45)
    sair_color    = cor_accent
    sair_shadow   = _hex_rgba(cor_primary, 0.20)
    sair_hover_bg = f"linear-gradient(135deg,{_hex_rgba(cor_primary,0.55)},{_hex_rgba(cor_primary,0.40)})"
    sair_hover_bd = _hex_rgba(cor_accent, 0.75)
    sair_glow     = _hex_rgba(cor_primary, 0.40)

    st.markdown(f"""
<style>
/* ── Botão SAIR ─────────────────────────────────────── */
section[data-testid="stSidebar"]
  div[data-testid="stButton"]:has(button[data-testid="sb_logout_btn"]) > button,
section[data-testid="stSidebar"]
  div[data-testid="stButton"]:has(button[data-testid="sb_logout_btn"]) > button p {{
    background:{sair_bg} !important; color:{sair_color} !important;
    border:1px solid {sair_border} !important; border-radius:12px !important;
    font-weight:600 !important; font-size:.82rem !important;
    letter-spacing:.4px !important; min-height:42px !important;
    transition:all .2s cubic-bezier(.16,1,.3,1) !important;
    box-shadow:0 2px 10px {sair_shadow},inset 0 1px 0 rgba(255,255,255,.06) !important;
}}
section[data-testid="stSidebar"]
  div[data-testid="stButton"]:has(button[data-testid="sb_logout_btn"]) > button:hover,
section[data-testid="stSidebar"]
  div[data-testid="stButton"]:has(button[data-testid="sb_logout_btn"]) > button:hover p {{
    background:{sair_hover_bg} !important; color:#fff !important;
    border-color:{sair_hover_bd} !important;
    box-shadow:0 0 22px {sair_glow},0 4px 14px {sair_shadow} !important;
    transform:translateY(-1px) !important;
}}
section[data-testid="stSidebar"]
  div[data-testid="stButton"]:has(button[data-testid="sb_logout_btn"]) > button:active {{
    transform:translateY(0px) !important;
    box-shadow:0 0 10px {sair_shadow} !important;
}}
</style>
""", unsafe_allow_html=True)

    st.sidebar.html(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Syne:wght@700;800&display=swap');
    section[data-testid="stSidebar"] > div {{
      background:
        radial-gradient(ellipse at 10% 10%, {p_20} 0%, transparent 55%),
        radial-gradient(ellipse at 90% 85%, rgba(0,245,255,.07) 0%, transparent 50%),
        linear-gradient(180deg,#0a0015 0%,#110028 55%,#0a0015 100%) !important;
    }}
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarNavSeparator"],
    [data-testid="stSidebarNavItems"] {{ display:none !important; }}
    section[data-testid="stSidebar"] [data-testid="stPageLink"] a,
    section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {{
      display:flex !important; align-items:center !important; gap:8px !important;
      padding:9px 14px !important; margin:1px 6px !important;
      border-radius:10px !important; border:1px solid transparent !important;
      font-family:'Inter',sans-serif !important; font-size:.86rem !important;
      font-weight:500 !important; color:rgba(255,255,255,.78) !important;
      text-decoration:none !important; transition:all .18s ease !important;
      background:transparent !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {{
      color:#fff !important; background:{a_12} !important;
      border-color:{a_25} !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"] {{
      color:#fff !important;
      background:linear-gradient(135deg,{p_32},{a_12}) !important;
      border-color:{a_45} !important;
      font-weight:600 !important; box-shadow:0 0 14px {a_15} !important;
    }}
    .hip-sidebar-divider {{
      height:1px; margin:14px 16px 10px;
      background:linear-gradient(90deg,transparent,{a_45},rgba(0,245,255,.15),transparent);
      border:none;
    }}
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {{ color:rgba(255,255,255,.75); }}
    section[data-testid="stSidebar"] strong {{ color:#fff; }}
    section[data-testid="stSidebar"] ::-webkit-scrollbar {{ width:4px; }}
    section[data-testid="stSidebar"] ::-webkit-scrollbar-track {{ background:transparent; }}
    section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {{
      background:{p_50}; border-radius:4px;
    }}

    /* ── Item Chiara: link nativo ────────────────────── */
    .chiara-nav-item {{
      display: flex !important;
      align-items: center !important;
      gap: 10px !important;
      padding: 8px 14px !important;
      margin: 1px 6px !important;
      border-radius: 10px !important;
      border: 1px solid {_hex_rgba(cor_accent, 0.30)} !important;
      background: linear-gradient(135deg,{_hex_rgba(cor_primary, 0.20)},{_hex_rgba(cor_accent, 0.09)}) !important;
      text-decoration: none !important;
      cursor: pointer !important;
      transition: all .18s ease !important;
      box-sizing: border-box !important;
    }}
    .chiara-nav-item:hover {{
      border-color: {_hex_rgba(cor_accent, 0.60)} !important;
      box-shadow: 0 0 16px {_hex_rgba(cor_primary, 0.30)} !important;
      background: linear-gradient(135deg,{_hex_rgba(cor_primary, 0.30)},{_hex_rgba(cor_accent, 0.15)}) !important;
    }}
    .chiara-nav-avatar {{
      width: 28px !important;
      height: 28px !important;
      border-radius: 50% !important;
      object-fit: cover !important;
      flex-shrink: 0 !important;
      border: 1.5px solid {_hex_rgba(cor_accent, 0.70)} !important;
      display: block !important;
    }}
    .chiara-nav-avatar-fallback {{
      width: 28px !important;
      height: 28px !important;
      border-radius: 50% !important;
      flex-shrink: 0 !important;
      background: linear-gradient(135deg,{cor_primary},{cor_accent}) !important;
      border: 1.5px solid {_hex_rgba(cor_accent, 0.55)} !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      font-size: .78rem !important;
      font-weight: 800 !important;
      color: #fff !important;
      font-family: 'Inter', sans-serif !important;
      line-height: 1 !important;
    }}
    .chiara-nav-nome {{
      font-size: .86rem !important;
      font-weight: 600 !important;
      color: #fff !important;
      white-space: nowrap !important;
      overflow: hidden !important;
      text-overflow: ellipsis !important;
      flex: 1 !important;
      min-width: 0 !important;
      font-family: 'Inter', sans-serif !important;
      line-height: 1 !important;
    }}
    .chiara-nav-badge {{
      font-size: .54rem !important;
      font-weight: 700 !important;
      letter-spacing: .6px !important;
      text-transform: uppercase !important;
      background: {_hex_rgba(cor_primary, 0.38)} !important;
      color: {cor_accent} !important;
      border: 1px solid {_hex_rgba(cor_accent, 0.40)} !important;
      padding: 2px 7px !important;
      border-radius: 999px !important;
      flex-shrink: 0 !important;
      line-height: 1.4 !important;
    }}
    </style>
    """)


def _build_user_avatar_html(display_nm: str, avatar_b64: str | None, badge_color: str = "#7c3aed") -> str:
    if avatar_b64:
        src = avatar_b64 if avatar_b64.startswith("data:") else f"data:image/jpeg;base64,{avatar_b64}"
        return (
            f'<img src="{src}" '
            f'style="width:38px;height:38px;border-radius:50%;object-fit:cover;'
            f'flex-shrink:0;border:1.5px solid {badge_color};" alt="avatar" />'
        )
    initial = (display_nm or "U")[0].upper()
    return (
        f'<div style="width:38px;height:38px;border-radius:50%;flex-shrink:0;'
        f'background:linear-gradient(135deg,{badge_color},{badge_color}88);'
        f'border:1.5px solid {badge_color}44;'
        f'display:flex;align-items:center;justify-content:center;'
        f'font-size:1rem;font-weight:800;color:#fff;">'
        f'{initial}</div>'
    )


def _build_chiara_menu_item(cor_primary: str, cor_accent: str) -> None:
    """
    Renderiza o item Chiara como um único bloco HTML com <a href> nativo.
    Estrutura visual:
      [ avatar 28x28 ] [ nome ] [ badge IA ]
    Todo o item é um único st.sidebar.html() — sem page_link separado,
    eliminando o problema de elementos Streamlit empilhados verticalmente.
    """
    foto_b64  = st.session_state.get("chiara_foto_b64", "") or ""
    foto_mime = st.session_state.get("chiara_foto_mime", "image/jpeg") or "image/jpeg"
    nome      = st.session_state.get("chiara_nome", "Chiara") or "Chiara"

    # Monta o avatar HTML
    if foto_b64:
        src = foto_b64 if foto_b64.startswith("data:") else f"data:{foto_mime};base64,{foto_b64}"
        avatar_html = f'<img src="{src}" alt="{nome}" class="chiara-nav-avatar" />'
    else:
        avatar_html = f'<div class="chiara-nav-avatar-fallback">C</div>'

    # HTML completo do item: um único bloco, sem depender de nenhum widget Streamlit
    # O <a> usa href relativo que o Streamlit Cloud interpreta corretamente
    st.sidebar.html(f"""
    <a href="/IA_Consultora" target="_self" class="chiara-nav-item">
      {avatar_html}
      <span class="chiara-nav-nome">{nome}</span>
      <span class="chiara-nav-badge">IA</span>
    </a>
    """)


def build_sidebar(
    show_cart: bool = True,
    cart_count: int = 0,
    cart_total: float = 0.0,
) -> None:
    perfil     = _normalize_role(st.session_state.get("perfil", "demo"))
    st.session_state["perfil"] = perfil

    cor_primary = st.session_state.get("tema_primary", "#7c3aed")
    cor_accent  = st.session_state.get("tema_accent",  "#b983ff")

    _inject_sidebar_css()
    _debug_sidebar_state(perfil)

    # Logo
    st.sidebar.html(f"""
    <div style="display:flex;align-items:center;gap:11px;padding:20px 16px 14px;">
      <div style="width:38px;height:38px;border-radius:11px;flex-shrink:0;
        background:linear-gradient(135deg,{cor_primary},#5b21b6);
        display:flex;align-items:center;justify-content:center;
        font-family:'Syne',sans-serif;font-weight:800;font-size:1.1rem;color:#fff;
        box-shadow:0 0 18px rgba(124,58,237,.6),0 0 40px rgba(185,131,255,.15);">H</div>
      <div>
        <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:.95rem;
          background:linear-gradient(90deg,#fff 20%,{cor_accent} 100%);
          -webkit-background-clip:text;-webkit-text-fill-color:transparent;
          background-clip:text;letter-spacing:.4px;line-height:1.1;">HIPNUS</div>
        <div style="font-family:'Inter',sans-serif;font-size:.53rem;
          color:rgba(185,131,255,.5);letter-spacing:3px;
          text-transform:uppercase;margin-top:2px;">Cosm&eacute;ticos</div>
      </div>
    </div>
    <div style="height:1px;margin:0 16px 8px;
      background:linear-gradient(90deg,transparent,{cor_accent}44,transparent);"></div>
    """)

    # Card usuário
    nome       = st.session_state.get("nome", "Visitante")
    display_nm = st.session_state.get("display_name", "") or nome
    avatar_b64 = st.session_state.get("avatar_b64", "")
    role_label = perfil.replace("_", " ").upper()

    badge_map = {
        "super_admin": "#7c3aed",
        "admin":       "#2563eb",
        "b2b":         "#059669",
        "b2c":         "#d97706",
        "demo":        "#6b7280",
    }
    badge_color = badge_map.get(perfil, cor_primary)
    avatar_html = _build_user_avatar_html(display_nm, avatar_b64, badge_color)

    st.sidebar.html(f"""
    <div style="display:flex;align-items:center;gap:10px;
      padding:10px 12px;margin:0 8px 8px;
      background:linear-gradient(135deg,{cor_primary}33,{cor_accent}11);
      border:1px solid {cor_accent}28;border-radius:14px;">
      {avatar_html}
      <div style="min-width:0;">
        <div style="font-family:'Inter',sans-serif;font-weight:700;font-size:.84rem;
          color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
          max-width:130px;line-height:1.3;" title="{display_nm}">{display_nm}</div>
        <div style="display:inline-block;margin-top:4px;
          background:linear-gradient(135deg,{cor_primary}99,{cor_primary}cc);
          color:#fff;font-size:.56rem;font-weight:700;
          letter-spacing:.8px;padding:2px 9px;border-radius:999px;
          text-transform:uppercase;">{role_label}</div>
      </div>
    </div>
    """)

    # Itens de menu
    for page_path, label, roles_ok in _NAV_ITEMS:
        if perfil not in roles_ok:
            continue
        if label == "__chiara__":
            _build_chiara_menu_item(cor_primary, cor_accent)
            continue
        lbl = f"{label}  ({cart_count})" if "Carrinho" in label and cart_count > 0 else label
        try:
            st.sidebar.page_link(page_path, label=lbl)
        except Exception:
            pass

    # Divider + SAIR
    st.sidebar.html('<hr class="hip-sidebar-divider">')
    with st.sidebar:
        if st.button(
            "⬡  Sair da plataforma",
            key="sb_logout_btn",
            use_container_width=True,
            help="Encerrar sessão e voltar ao login",
        ):
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
