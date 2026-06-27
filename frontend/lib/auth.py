"""
auth.py — HIPNUS COSMÉTICOS
==============================
Guarda de autenticação 100% offline — SEM chamadas ao FastAPI.

Aceita login por USERNAME ou E-MAIL:
  - Usuarios demo/seed: buscados no dicionario USUARIOS_DEMO
  - Parceiros cadastrados via convite: buscados no banco SQLite
    (tabela 'parceiros' quando implementada, ou fallback por e-mail
     nos registros de invites marcados como usados)

Roles disponíveis:
  super_admin : acesso total (William / dev)
  admin       : administrador da Hipnus
  b2b         : parceiro profissional / salão
  b2c         : cliente final
  demo        : modo demonstração (somente leitura)
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
    })


# ─── Busca usuário por username OU e-mail nos USUARIOS_DEMO ──────────────────
def _buscar_demo(identificador: str) -> tuple[str, dict] | None:
    """
    Busca nos USUARIOS_DEMO por username (chave) ou por e-mail.
    Retorna (username, dados) ou None.
    """
    ident = identificador.strip().lower()
    # Por username
    if ident in USUARIOS_DEMO:
        return ident, USUARIOS_DEMO[ident]
    # Por e-mail
    for uname, dados in USUARIOS_DEMO.items():
        if dados.get("email", "").lower() == ident:
            return uname, dados
    return None


# ─── Busca parceiro cadastrado via convite no banco SQLite ─────────────────
def _buscar_parceiro_db(email: str, senha: str) -> dict | None:
    """
    Busca parceiro cadastrado via convite no banco SQLite.
    Usa a tabela 'parceiros' se existir; caso contrario, usa 'invites'
    para confirmar que o e-mail tem um convite usado.

    Retorna dict com dados do parceiro ou None se nao encontrado.
    """
    try:
        import sys
        from pathlib import Path
        _root = Path(__file__).resolve().parents[2]
        if str(_root) not in sys.path:
            sys.path.insert(0, str(_root))

        from lib.db_utils import get_db_session
        from sqlalchemy import text

        db, _ = get_db_session()
        if not db:
            return None

        try:
            # Tentativa 1: tabela 'parceiros' (criada pelo cadastro completo)
            row = db.execute(
                text("""
                    SELECT nome, email, role, telefone, empresa
                    FROM parceiros
                    WHERE email = :email AND senha_hash = :senha
                """),
                {"email": email.lower().strip(), "senha": senha},
            ).fetchone()
            if row:
                d = dict(row._mapping)
                return {
                    "nome":         d.get("nome", email),
                    "username":     d.get("email", email),
                    "role":         d.get("role", "b2b"),
                    "display_name": d.get("empresa") or d.get("nome", ""),
                    "email":        d.get("email", email),
                }
        except Exception:
            pass

        # Tentativa 2: verifica se e-mail tem convite USADO (cadastro concluido)
        # Neste caso, aceita qualquer senha por enquanto (sem tabela parceiros ainda)
        try:
            row = db.execute(
                text("""
                    SELECT email, role FROM invites
                    WHERE email = :email AND used = 1
                    LIMIT 1
                """),
                {"email": email.lower().strip()},
            ).fetchone()
            if row:
                d = dict(row._mapping)
                nome_base = email.split("@")[0].capitalize()
                return {
                    "nome":         nome_base,
                    "username":     d.get("email", email),
                    "role":         d.get("role", "b2b"),
                    "display_name": nome_base,
                    "email":        d.get("email", email),
                }
        except Exception:
            pass

        return None
    except Exception:
        return None
    finally:
        try:
            db.close()
        except Exception:
            pass


# ─── Login offline ───────────────────────────────────────────────────────────
def _login_offline(identificador: str, password: str) -> bool:
    """
    Valida credenciais por USERNAME ou E-MAIL.

    Ordem de busca:
      1. USUARIOS_DEMO (username ou e-mail)
      2. Banco SQLite — parceiros cadastrados via convite

    Retorna True e grava sessão em caso de sucesso.
    """
    # ─ Busca nos usuarios demo/seed ─────────────────────────────────
    encontrado = _buscar_demo(identificador)
    if encontrado:
        uname, u = encontrado
        if password == u["senha"]:
            _gravar_sessao(
                nome=u["nome"],
                username=uname,
                role=u["role"],
                display_name=u["display_name"],
                email=u["email"],
                token=None,
                via_api=False,
            )
            return True
        return False  # usuário encontrado mas senha errada

    # ─ Busca no banco (parceiros via convite) ────────────────────────
    # So tenta se parece com e-mail
    if "@" in identificador:
        parceiro = _buscar_parceiro_db(identificador, password)
        if parceiro:
            _gravar_sessao(
                nome=parceiro["nome"],
                username=parceiro["username"],
                role=parceiro["role"],
                display_name=parceiro["display_name"],
                email=parceiro["email"],
                token=None,
                via_api=False,
            )
            return True

    return False


# ─── Login público ───────────────────────────────────────────────────────────
def fazer_login(identificador: str, password: str) -> tuple[bool, str]:
    """
    Autentica por USERNAME ou E-MAIL + senha.

    Exemplos válidos:
      fazer_login("william", "hipnus@2026")            # username
      fazer_login("admin@hipnuscosmeticos.com.br", ...) # e-mail
      fazer_login("parceiro@email.com", ...)            # e-mail de convite usado
    """
    if _login_offline(identificador, password):
        encontrado = _buscar_demo(identificador)
        if encontrado:
            nome = encontrado[1]["nome"]
        else:
            nome = identificador.split("@")[0].capitalize()
        return True, f"Bem-vindo(a), {nome}!"

    return False, "Usuário/e-mail ou senha incorretos."


# ─── require_auth ──────────────────────────────────────────────────────────
def require_auth(perfis_permitidos: list[str] | None = None) -> dict:
    """
    Protege a página exigindo autenticação.
    Redireciona para streamlit_app.py se não autenticado.
    """
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
    }

    if perfis_permitidos and usuario["perfil"] not in perfis_permitidos:
        st.error("🚫 Você não tem permissão para acessar esta página.")
        st.stop()

    return usuario


def logout() -> None:
    """Limpa a sessão e redireciona para o login."""
    for key in [
        "autenticado", "usuario", "perfil", "nome",
        "display_name", "email", "token", "via_api",
    ]:
        st.session_state.pop(key, None)
    st.query_params.clear()
    st.switch_page(_LOGIN_PAGE)


# ─── Componentes de sidebar ─────────────────────────────────────────────────
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

    icone  = {"super_admin": "⭐", "admin": "🛡️", "b2b": "🎤", "b2c": "👤", "demo": "👀"}.get(perfil, "👤")
    fonte  = "API" if via_api else "offline"
    label  = display_name if display_name else nome

    st.sidebar.html(
        f"""
        <style>
        section[data-testid="stSidebar"] .stHtml:has(.hip-sidebar-user) {{
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }}
        section[data-testid="stSidebar"] .stHtml:has(.hip-sidebar-user) + div {{
            margin-top: 0 !important;
            padding-top: 0 !important;
        }}
        </style>
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
    #hip-logout-btn:hover {
        background: #3d1a78; color: #ffffff; border-color: #3d1a78;
    }
    </style>
    <div id="hip-logout-btn-wrap">
        <a id="hip-logout-btn"
           href="?logout=1"
           onclick="window.parent.location.href='?logout=1'; return false;">
            🚶 Sair
        </a>
    </div>
    """)
