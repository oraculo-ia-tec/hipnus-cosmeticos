"""
auth.py — HIPNUS COSMÉTICOS
==============================
Guarda de autenticação — aceita USERNAME ou E-MAIL.
Exibe avatar do usuário no sidebar (imagem circular).
"""
from __future__ import annotations

import streamlit as st

ROLES_PRIVILEGIADOS = {"super_admin", "admin"}
ROLES_PROFISSIONAIS = {"super_admin", "admin", "b2b"}

LOGIN_PAGE  = "streamlit_app.py"
HOME_PAGE   = "pages/1_Home.py"
_LOGIN_PAGE = LOGIN_PAGE
_HOME_PAGE  = HOME_PAGE


# ─── Usuários demo/seed ─────────────────────────────────────────────────────────
USUARIOS_DEMO: dict[str, dict] = {
    "william": {
        "senha":        "hipnus@2026",
        "role":         "super_admin",
        "nome":         "William Eustáquio",
        "display_name": "Desenvolvedor de IA",
        "email":        "programador.descpro@gmail.com",
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


# ─── Helpers de sessão ─────────────────────────────────────────────────────────
def _gravar_sessao(
    nome: str,
    username: str,
    role: str,
    display_name: str,
    email: str,
    token: str | None,
    via_api: bool,
    avatar_b64: str | None = None,
) -> None:
    st.session_state.update({
        "autenticado":  True,
        "usuario":      username,
        "nome":         nome,
        "perfil":       role,
        "display_name": display_name,
        "email":        email,
        "token":        token,
        "via_api":      via_api,
        "avatar_b64":   avatar_b64,
    })


# ─── Busca por username OU e-mail nos USUARIOS_DEMO ───────────────────────
def _buscar_demo(identificador: str) -> tuple[str, dict] | None:
    ident = identificador.strip().lower()
    if ident in USUARIOS_DEMO:
        return ident, USUARIOS_DEMO[ident]
    for uname, dados in USUARIOS_DEMO.items():
        if dados.get("email", "").lower() == ident:
            return uname, dados
    return None


# ─── Busca parceiro no banco SQLite ─────────────────────────────────────────
def _buscar_parceiro_db(email: str, senha: str) -> dict | None:
    """Autentica parceiro via tabela 'parceiros' (com senha_hash)."""
    try:
        import sys
        from pathlib import Path
        _root = Path(__file__).resolve().parents[2]
        if str(_root) not in sys.path:
            sys.path.insert(0, str(_root))

        from lib.user_db import autenticar_parceiro
        return autenticar_parceiro(email, senha)
    except Exception:
        pass

    # Fallback: invite used (sem tabela parceiros)
    try:
        from lib.db_utils import get_db_session
        from sqlalchemy import text
        db, _ = get_db_session()
        if not db:
            return None
        row = db.execute(
            text("SELECT email, role FROM invites WHERE email = :e AND used = 1 LIMIT 1"),
            {"e": email.lower().strip()},
        ).fetchone()
        db.close()
        if row:
            d = dict(row._mapping)
            nome_base = email.split("@")[0].capitalize()
            return {
                "nome": nome_base, "username": d["email"],
                "role": d.get("role", "b2b"), "display_name": nome_base,
                "email": d["email"], "avatar_b64": None,
            }
    except Exception:
        pass
    return None


# ─── Login offline ───────────────────────────────────────────────────────────
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


# ─── Login público ───────────────────────────────────────────────────────────
def fazer_login(identificador: str, password: str) -> tuple[bool, str]:
    if _login_offline(identificador, password):
        encontrado = _buscar_demo(identificador)
        nome = encontrado[1]["nome"] if encontrado else identificador.split("@")[0].capitalize()
        return True, f"Bem-vindo(a), {nome}!"
    return False, "Usuário/e-mail ou senha incorretos."


# ─── require_auth ──────────────────────────────────────────────────────────
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
    ]:
        st.session_state.pop(key, None)
    st.query_params.clear()
    st.switch_page(_LOGIN_PAGE)


# ─── Sidebar ────────────────────────────────────────────────────────────────────
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
    """
    Card do usuário na sidebar.
    Exibe foto de perfil circular (se houver) + nome + role.
    A mesma avatar_b64 será usada futuramente no chat da IA Consultora.
    """
    nome         = st.session_state.get("nome", "Visitante")
    display_name = st.session_state.get("display_name", "")
    perfil       = st.session_state.get("perfil", "demo")
    via_api      = st.session_state.get("via_api", False)
    avatar_b64   = st.session_state.get("avatar_b64", None)

    icone_fallback = {"super_admin": "⭐", "admin": "🛡️", "b2b": "🎤", "b2c": "👤", "demo": "👀"}.get(perfil, "👤")
    fonte  = "API" if via_api else "offline"
    label  = display_name if display_name else nome
    role_label = perfil.replace("_", " ").upper()

    # Bloco do avatar: imagem circular se existir, emoji caso contrário
    if avatar_b64:
        avatar_html = (
            f'<img src="{avatar_b64}" '
            f'style="width:52px;height:52px;border-radius:50%;object-fit:cover;'
            f'border:2.5px solid rgba(255,255,255,.5);flex-shrink:0;" />'
        )
    else:
        avatar_html = (
            f'<div style="width:52px;height:52px;border-radius:50%;'
            f'background:rgba(255,255,255,.15);border:2px solid rgba(255,255,255,.3);'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-size:1.4rem;flex-shrink:0;">{icone_fallback}</div>'
        )

    st.sidebar.html(
        f"""
        <style>
        section[data-testid="stSidebar"] .stHtml:has(.hip-sidebar-user) {{
            margin-bottom: 0 !important; padding-bottom: 0 !important;
        }}
        </style>
        <div class="hip-sidebar-user" style="
            display:flex; align-items:center; gap:10px;
            background:rgba(124,58,237,.18); border:1px solid rgba(124,58,237,.3);
            border-radius:14px; padding:10px 12px; margin:0 0 4px;
        ">
            {avatar_html}
            <div style="min-width:0;">
                <div style="font-weight:700;font-size:.9rem;color:#fff;
                            white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:130px;"
                     title="{label}">{label}</div>
                <div style="display:flex;gap:6px;margin-top:4px;flex-wrap:wrap;">
                    <span style="background:rgba(124,58,237,.5);color:#e9d5ff;
                                 font-size:.6rem;font-weight:700;letter-spacing:.8px;
                                 padding:2px 8px;border-radius:999px;">{role_label}</span>
                    <span style="background:rgba(255,255,255,.1);color:rgba(255,255,255,.6);
                                 font-size:.6rem;padding:2px 8px;border-radius:999px;">{fonte}</span>
                </div>
            </div>
        </div>
        """
    )


def sidebar_logout_button() -> None:
    st.sidebar.html("""
    <style>
    #hip-logout-btn-wrap {
        position: fixed; bottom: 20px; left: 0;
        width: 244px; padding: 0 14px;
        z-index: 99999; box-sizing: border-box;
    }
    #hip-logout-btn {
        display: flex; align-items: center; justify-content: center;
        gap: 8px; width: 100%; padding: 12px 0;
        background: #ffffff; color: #3d1a78;
        border: 1.5px solid #d0c4f0; border-radius: 10px;
        font-size: 1rem; font-weight: 700; cursor: pointer;
        transition: background .18s, color .18s, border-color .18s;
        text-decoration: none; letter-spacing: .01em; box-sizing: border-box;
    }
    #hip-logout-btn:hover { background: #3d1a78; color: #ffffff; border-color: #3d1a78; }
    </style>
    <div id="hip-logout-btn-wrap">
        <a id="hip-logout-btn" href="?logout=1"
           onclick="window.parent.location.href='?logout=1'; return false;">
            🚶 Sair
        </a>
    </div>
    """)
