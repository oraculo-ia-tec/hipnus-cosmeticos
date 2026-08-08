"""
auth.py — TÁLYA COSMÉTICOS
==============================
v13 — 2026-07-01:
  - fix: _gravar_sessao NÃO zera chiara_foto_b64/mime ao fazer login.
    Antes, cada login apagava a foto da Chiara do session_state,
    forçando recarregar do banco na próxima página. Agora preserva
    valores já carregados se existirem.
  - fix: _restaurar_avatar_usuario normaliza o valor lido do banco
    para data-URI completo (data:image/jpeg;base64,...), garantindo
    que <img src> funcione corretamente após restauração de sessão.
  - fix: remove capa branca do botão SAIR (v12 mantido).
"""
from __future__ import annotations

from pathlib import Path
import streamlit as st

ROLES_PRIVILEGIADOS = {"super_admin", "admin"}
ROLES_PROFISSIONAIS = {"super_admin", "admin", "b2b"}

# Caminhos absolutos evitam falha de resolução no Streamlit Cloud
_APP_ROOT   = Path(__file__).resolve().parents[2]
LOGIN_PAGE  = str(_APP_ROOT / "login.py")
HOME_PAGE   = str(_APP_ROOT / "frontend" / "pages" / "0_🏠_Home.py")
_LOGIN_PAGE = LOGIN_PAGE
_HOME_PAGE  = HOME_PAGE

DEBUG_SIDEBAR = False


# ─── Usuários demo/seed ────────────────────────────────────────────────────────
# Credenciais carregadas de st.secrets ou variáveis de ambiente.
# NUNCA coloque senhas hardcoded neste arquivo.
# Configure as variáveis no .env ou no painel Secrets do Streamlit Cloud.
def _load_demo_users() -> dict[str, dict]:
    """
    Carrega usuários demo a partir de st.secrets ou variáveis de ambiente.

    Formato esperado em .env:
      DEMO_USER_WILLIAM=william:hipnus@2026:super_admin:William Eustáquio:programador.descpro@gmail.com

    Cada variável DEMO_USER_* tem o formato: username:senha:role:nome:email
    """
    import os
    users: dict[str, dict] = {}
    try:
        import streamlit as st
        src = dict(st.secrets.get("demo_users", {}))
    except Exception:
        src = {}

    # Fallback: ler variáveis DEMO_USER_* do ambiente
    for key, value in os.environ.items():
        if key.startswith("DEMO_USER_") and value:
            parts = value.split(":", 4)
            if len(parts) >= 2:
                uname = parts[0]
                if uname not in src:
                    src[uname] = ":".join(parts[1:])

    for uname, raw in src.items():
        if isinstance(raw, dict):
            users[uname] = raw
        elif isinstance(raw, str):
            parts = raw.split(":", 4)
            users[uname] = {
                "senha":        parts[0] if len(parts) > 0 else "",
                "role":         parts[1] if len(parts) > 1 else "b2c",
                "nome":         parts[2] if len(parts) > 2 else uname,
                "display_name": parts[3] if len(parts) > 3 else uname,
                "email":        parts[4] if len(parts) > 4 else f"{uname}@talyacosmeticos.com.br",
            }
    return users


USUARIOS_DEMO: dict[str, dict] = _load_demo_users()


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


def _normalize_avatar(raw: str | None) -> str | None:
    """
    Garante que o avatar esteja no formato data-URI completo.
    Se o banco retornar base64 puro (sem prefixo), adiciona o prefixo JPEG.
    Se já começar com 'data:' retorna sem alteração.
    """
    if not raw:
        return None
    if raw.startswith("data:"):
        return raw
    # base64 puro — adiciona prefixo JPEG como default seguro
    return f"data:image/jpeg;base64,{raw}"


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
    """
    Restaura o avatar do usuário do banco após reinicialização de sessão.
    Normaliza o valor para data-URI completo antes de salvar no session_state,
    garantindo que <img src> funcione corretamente.
    """
    if st.session_state.get("avatar_b64"):
        # Já existe na sessão — garante que está em data-URI
        current = st.session_state["avatar_b64"]
        if current and not current.startswith("data:"):
            st.session_state["avatar_b64"] = f"data:image/jpeg;base64,{current}"
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
            st.session_state["avatar_b64"] = _normalize_avatar(parceiro["avatar_b64"])
    except Exception:
        pass


def _gravar_sessao(
    nome: str, username: str, role: str,
    display_name: str, email: str, token: str | None,
    via_api: bool, avatar_b64: str | None = None,
) -> None:
    """
    Grava os dados da sessão após login.
    IMPORTANTE: NÃO zera chiara_foto_b64/mime se já estiverem carregados
    no session_state — evita perda da foto da Chiara a cada login.
    O avatar do usuário é normalizado para data-URI antes de gravar.
    """
    import time

    # Preserva Chiara se já carregado (não zera no login)
    chiara_b64  = st.session_state.get("chiara_foto_b64")  or None
    chiara_mime = st.session_state.get("chiara_foto_mime") or None
    chiara_nome = st.session_state.get("chiara_nome")      or None
    chiara_cargo= st.session_state.get("chiara_cargo")     or None
    chiara_sau  = st.session_state.get("chiara_saudacao")  or None

    st.session_state.update({
        "autenticado":       True,
        "usuario":           username,
        "nome":              nome,
        "perfil":            _normalize_role(role),
        "display_name":      display_name,
        "email":             email,
        "token":             token,
        "via_api":           via_api,
        # Avatar normalizado para data-URI
        "avatar_b64":        _normalize_avatar(avatar_b64),
        "session_start":     time.time(),
        "_jwt_dialog_shown": False,
        # Chiara: preserva valores existentes ou None (serão carregados por _carregar_chiara_no_session)
        "chiara_foto_b64":   chiara_b64,
        "chiara_foto_mime":  chiara_mime,
        "chiara_nome":       chiara_nome,
        "chiara_cargo":      chiara_cargo,
        "chiara_saudacao":   chiara_sau,
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


def _login_supabase(identificador: str, password: str) -> bool:
    """Autentica contra Supabase Auth; suporta username ou e-mail."""
    import logging
    try:
        from lib.supabase_client import get_supabase
        sb = get_supabase()

        # Resolve username → email via RPC SECURITY DEFINER (bypassa RLS)
        email = identificador
        if "@" not in identificador:
            rpc_res = sb.rpc("get_email_by_username", {"p_username": identificador.lower()}).execute()
            if not rpc_res.data:
                return False
            email = rpc_res.data

        auth_resp = sb.auth.sign_in_with_password({"email": email, "password": password})
        if not auth_resp.user:
            return False

        # Usa metadados do auth.users — evita query separada e incompatibilidade de API v2
        meta = auth_resp.user.user_metadata or {}
        _gravar_sessao(
            nome=meta.get("name") or email.split("@")[0].capitalize(),
            username=meta.get("username") or identificador,
            role=meta.get("role", "b2c"),
            display_name=meta.get("name") or "",
            email=email,
            token=auth_resp.session.access_token if auth_resp.session else None,
            via_api=False,
        )
        return True
    except Exception as exc:
        logging.warning("_login_supabase falhou: %s", exc)
        return False


def fazer_login(identificador: str, password: str) -> tuple[bool, str]:
    if _login_offline(identificador, password):
        encontrado = _buscar_demo(identificador)
        nome = encontrado[1]["nome"] if encontrado else identificador.split("@")[0].capitalize()
        return True, f"Bem-vindo(a), {nome}!"
    if _login_supabase(identificador, password):
        nome = st.session_state.get("nome", identificador.split("@")[0].capitalize())
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
    ("frontend/pages/10_🤖_IA_Consultora.py",   "__chiara__",            {"super_admin","admin","b2b","b2c","demo"}),
    ("frontend/pages/0_📊_Dashboard.py",         "📊  Dashboard",         {"super_admin","admin"}),
    ("frontend/pages/1_🛍️_Catálogo.py",          "🛍️  Catálogo",          {"super_admin","admin","b2b","b2c"}),
    ("frontend/pages/3_🏠_Loja_do_Parceiro.py",  "🏠  Loja Parceiro",     {"super_admin","admin","b2b"}),
    ("frontend/pages/4_🛒_Carrinho.py",           "🛒  Carrinho",          {"super_admin","admin","b2b","b2c"}),
    ("frontend/pages/5_💳_Checkout.py",           "💳  Checkout",          {"super_admin","admin","b2b","b2c"}),
    ("frontend/pages/6_Convites.py",              "✉️  Convites",          {"super_admin","admin"}),
    ("frontend/pages/7_Cadastro_Parceiro.py",     "➕  Cadastro Parceiro", {"super_admin","admin"}),
    ("frontend/pages/8_Configuracao.py",          "⚙️  Configurações",     {"super_admin","admin"}),
    ("frontend/pages/9_👥_Usuarios.py",          "👥  Usuários",          {"super_admin"}),
    ("frontend/pages/11_Onboarding.py",           "🔖  Onboarding",        {"super_admin","admin"}),
    ("frontend/pages/11_🏠_Minha_Loja_Config.py", "🏪  Minha Loja",        {"super_admin","admin","b2b"}),
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
    try:
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    except Exception:
        return f"rgba(124,58,237,{alpha})"


def _inject_sidebar_css() -> None:
    # Paleta fixa Tálya (ignora tema_primary/accent na sidebar)
    st.markdown("""
<style>
section[data-testid="stSidebar"]
  div[data-testid="stButton"]:has(button[data-testid="sb_logout_btn"]) > button {
    background:linear-gradient(135deg,#b76e79dd,#c9a04eaa) !important;
    color:#fff !important;
    border:1px solid rgba(183,110,121,.45) !important;
    border-radius:10px !important;
    font-family:'Manrope',sans-serif !important;
    font-weight:600 !important;
    font-size:.86rem !important;
    letter-spacing:.3px !important;
    min-height:44px !important;
    transition:all .18s ease !important;
    box-shadow:0 2px 10px rgba(183,110,121,.25) !important;
}
section[data-testid="stSidebar"]
  div[data-testid="stButton"]:has(button[data-testid="sb_logout_btn"]) > button p {
    color:#fff !important;
    background:transparent !important;
}
section[data-testid="stSidebar"]
  div[data-testid="stButton"]:has(button[data-testid="sb_logout_btn"]) > button:hover {
    background:linear-gradient(135deg,#b76e79,#c9a04e) !important;
    color:#fff !important;
    border-color:#b76e79 !important;
    box-shadow:0 0 16px rgba(183,110,121,.45) !important;
    transform:translateY(-1px) !important;
}
section[data-testid="stSidebar"]
  div[data-testid="stButton"]:has(button[data-testid="sb_logout_btn"]) > button:hover p {
    color:#fff !important;
    background:transparent !important;
}
section[data-testid="stSidebar"]
  div[data-testid="stButton"]:has(button[data-testid="sb_logout_btn"]) > button:active {
    transform:translateY(0px) !important;
}
</style>
""", unsafe_allow_html=True)

    st.sidebar.html("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;500;600;700;800&family=Cormorant:ital,wght@0,400;0,600;0,700;1,500&display=swap');
    section[data-testid="stSidebar"] > div {
      background:
        radial-gradient(ellipse at 15% 5%,  rgba(183,110,121,.10) 0%, transparent 50%),
        radial-gradient(ellipse at 85% 90%, rgba(201,160,78,.07)  0%, transparent 50%),
        linear-gradient(180deg,#fbf6f2 0%,#f5ece4 60%,#f1e4da 100%) !important;
    }
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarNavSeparator"],
    [data-testid="stSidebarNavItems"] { display:none !important; }
    section[data-testid="stSidebar"] [data-testid="stPageLink"] a,
    section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {
      display:flex !important; align-items:center !important; gap:8px !important;
      padding:9px 14px !important; margin:1px 6px !important;
      border-radius:10px !important; border:1px solid transparent !important;
      font-family:'Manrope',sans-serif !important; font-size:.86rem !important;
      font-weight:500 !important; color:#3a2620 !important;
      text-decoration:none !important; transition:all .18s ease !important;
      background:transparent !important;
    }
    section[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
      color:#b76e79 !important;
      background:rgba(183,110,121,.09) !important;
      border-color:rgba(183,110,121,.22) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"] {
      color:#b76e79 !important;
      background:linear-gradient(135deg,rgba(183,110,121,.14),rgba(201,160,78,.07)) !important;
      border-color:rgba(183,110,121,.32) !important;
      font-weight:600 !important;
      box-shadow:0 2px 8px rgba(183,110,121,.12) !important;
    }
    .hip-sidebar-divider {
      height:1px; margin:14px 16px 10px;
      background:linear-gradient(90deg,transparent,rgba(183,110,121,.30),rgba(201,160,78,.15),transparent);
      border:none;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label { color:#6b4f43; }
    section[data-testid="stSidebar"] strong { color:#3a2620; }
    section[data-testid="stSidebar"] ::-webkit-scrollbar { width:4px; }
    section[data-testid="stSidebar"] ::-webkit-scrollbar-track { background:transparent; }
    section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
      background:rgba(183,110,121,.35); border-radius:4px;
    }
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
    foto_b64  = st.session_state.get("chiara_foto_b64", "") or ""
    foto_mime = st.session_state.get("chiara_foto_mime", "image/jpeg") or "image/jpeg"
    nome      = st.session_state.get("chiara_nome", "Tálya") or "Tálya"

    if foto_b64:
        src = foto_b64 if foto_b64.startswith("data:") else f"data:{foto_mime};base64,{foto_b64}"
        avatar_html = (
            f'<img src="{src}" alt="{nome}" '
            f'style="'
            f'width:32px;height:32px;border-radius:50%;object-fit:cover;'
            f'flex-shrink:0;display:block;'
            f'border:2px solid {_hex_rgba(cor_accent, 0.75)};'
            f'" />'
        )
    else:
        avatar_html = (
            f'<div style="'
            f'width:32px;height:32px;border-radius:50%;flex-shrink:0;'
            f'background:linear-gradient(135deg,{cor_primary},{cor_accent});'
            f'border:2px solid {_hex_rgba(cor_accent, 0.55)};'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-size:.8rem;font-weight:800;color:#fff;'
            f'font-family:Manrope,sans-serif;line-height:1;'
            f'">C</div>'
        )

    st.sidebar.html(f"""
    <style>
      *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
      body{{margin:0;padding:0;background:transparent;overflow:hidden;}}
      .chi-card{{
        display:flex;
        flex-direction:row;
        align-items:center;
        gap:10px;
        padding:7px 12px;
        margin:1px 6px;
        border-radius:10px;
        border:1px solid rgba(183,110,121,.28);
        background:linear-gradient(135deg,rgba(183,110,121,.12),rgba(201,160,78,.06));
        min-height:44px;
        pointer-events:none;
      }}
      .chi-nome{{
        flex:1;
        min-width:0;
        white-space:nowrap;
        overflow:hidden;
        text-overflow:ellipsis;
        font-family:Manrope,sans-serif;
        font-size:.86rem;
        font-weight:600;
        color:#3a2620;
        line-height:1;
      }}
      .chi-badge{{
        flex-shrink:0;
        font-family:Manrope,sans-serif;
        font-size:.54rem;
        font-weight:700;
        letter-spacing:.6px;
        text-transform:uppercase;
        background:linear-gradient(135deg,#b76e79cc,#c9a04e99);
        color:#fff;
        border:1px solid rgba(183,110,121,.40);
        padding:2px 7px;
        border-radius:999px;
        line-height:1.4;
      }}
    </style>
    <div class="chi-card">
      {avatar_html}
      <span class="chi-nome">{nome}</span>
      <span class="chi-badge">IA</span>
    </div>
    """)

    st.sidebar.markdown(
        """
        <style>
        section[data-testid="stSidebar"]
          div[data-testid="stPageLink"]:has(a[href*="IA_Consultora"]) {
            margin-top: -54px !important;
            opacity: 0 !important;
            height: 54px !important;
            pointer-events: all !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    try:
        st.sidebar.page_link("frontend/pages/10_🤖_IA_Consultora.py", label=nome)
    except Exception:
        pass


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
        background:linear-gradient(135deg,#b76e79,#c9a04e);
        display:flex;align-items:center;justify-content:center;
        font-family:'Cormorant',serif;font-weight:800;font-size:1.1rem;color:#fff;
        box-shadow:0 0 18px rgba(183,110,121,.45),0 0 40px rgba(201,160,78,.20);">T</div>
      <div>
        <div style="font-family:'Cormorant',serif;font-weight:800;font-size:.95rem;
          background:linear-gradient(90deg,#3a2620 20%,#b76e79 100%);
          -webkit-background-clip:text;-webkit-text-fill-color:transparent;
          background-clip:text;letter-spacing:.4px;line-height:1.1;">TÁLYA</div>
        <div style="font-family:'Manrope',sans-serif;font-size:.53rem;
          color:#a08876;letter-spacing:3px;
          text-transform:uppercase;margin-top:2px;">Cosm&eacute;ticos</div>
      </div>
    </div>
    <div style="height:1px;margin:0 16px 8px;
      background:linear-gradient(90deg,transparent,rgba(183,110,121,.35),rgba(201,160,78,.15),transparent);"></div>
    """)

    # Card usuário
    nome       = st.session_state.get("nome", "Visitante")
    display_nm = st.session_state.get("display_name", "") or nome
    avatar_b64 = st.session_state.get("avatar_b64", "")
    role_label = perfil.replace("_", " ").upper()

    badge_map = {
        "super_admin": "#b76e79",
        "admin":       "#c9a04e",
        "b2b":         "#7c5c4a",
        "b2c":         "#a08876",
        "demo":        "#6b4f43",
    }
    badge_color = badge_map.get(perfil, cor_primary)
    avatar_html = _build_user_avatar_html(display_nm, avatar_b64, badge_color)

    st.sidebar.html(f"""
    <div style="display:flex;align-items:center;gap:10px;
      padding:10px 12px 14px;margin:0 8px 8px;overflow:visible;
      background:linear-gradient(135deg,rgba(183,110,121,.12),rgba(201,160,78,.06));
      border:1px solid rgba(183,110,121,.22);border-radius:14px;">
      {avatar_html}
      <div style="min-width:0;padding-bottom:2px;">
        <div style="font-family:'Manrope',sans-serif;font-weight:700;font-size:.84rem;
          color:#3a2620;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
          max-width:130px;line-height:1.3;" title="{display_nm}">{display_nm}</div>
        <div style="display:inline-block;margin-top:4px;
          border:1px solid rgba(201,160,78,0.55);border-radius:999px;
          padding:2px 10px;background:rgba(201,160,78,0.06);">
          <span style="font-family:'Manrope',sans-serif;font-size:.56rem;font-weight:700;
            letter-spacing:1.2px;text-transform:uppercase;
            background:linear-gradient(90deg,#b76e79,#c9a04e);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
            background-clip:text;">{role_label}</span>
        </div>
      </div>
    </div>
    """)

    # Itens de menu
    _chiara_done = False
    for page_path, label, roles_ok in _NAV_ITEMS:
        if perfil not in roles_ok:
            continue
        if label == "__chiara__":
            _build_chiara_menu_item(cor_primary, cor_accent)
            _chiara_done = True
            continue
        if _chiara_done:
            st.sidebar.html('<hr class="hip-sidebar-divider">')
            _chiara_done = False
        lbl = f"{label}  ({cart_count})" if "Carrinho" in label and cart_count > 0 else label
        try:
            st.sidebar.page_link(page_path, label=lbl)
        except Exception:
            pass

    # Divider + SAIR
    st.sidebar.html('<hr class="hip-sidebar-divider">')
    with st.sidebar:
        if st.button(
            "⧡  Sair da plataforma",
            key="sb_logout_btn",
            use_container_width=True,
            help="Encerrar sessão e voltar ao login",
        ):
            logout()


# ─── Aliases de compatibilidade ─────────────────────────────────────────────────────────
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
