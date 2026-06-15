"""
auth.py — HIPNUS COSMÉTICOS
==============================
Guarda de autenticação para páginas protegidas.

Uso em qualquer página:
    from lib.auth import require_auth
    require_auth()   # bloqueia e redireciona se não autenticado

Perfis disponíveis:
    admin  — acesso total
    b2b    — profissional / salão / distribuidor
    b2c    — consumidor final
    demo   — vitrine pública (somente leitura)
"""
import streamlit as st


def require_auth(perfis_permitidos: list[str] | None = None) -> dict:
    """
    Verifica se o usuário está autenticado.
    Se não estiver, redireciona para a página de Login.
    Se perfis_permitidos for informado, bloqueia perfis não autorizados.

    Retorna o dicionário com dados do usuário logado.
    """
    if not st.session_state.get("autenticado"):
        st.switch_page("Login.py")

    usuario = {
        "login":  st.session_state.get("usuario", ""),
        "perfil": st.session_state.get("perfil",  "demo"),
        "nome":   st.session_state.get("nome",    "Visitante"),
    }

    if perfis_permitidos and usuario["perfil"] not in perfis_permitidos:
        st.error("🚫 Você não tem permissão para acessar esta página.")
        st.stop()

    return usuario


def logout() -> None:
    """Encerra a sessão e redireciona para a página de Login."""
    for key in ["autenticado", "usuario", "perfil", "nome"]:
        st.session_state.pop(key, None)
    st.switch_page("Login.py")


def sidebar_user_info() -> None:
    """
    Exibe o nome do usuário logado e botão de logout na sidebar.
    Chamar após require_auth().
    """
    usuario = st.session_state.get("nome", "Visitante")
    perfil  = st.session_state.get("perfil", "demo")

    icone = {"admin": "⭐", "b2b": "🏪", "b2c": "👤", "demo": "👀"}.get(perfil, "👤")

    st.sidebar.markdown(
        f"**{icone} {usuario}**  \n"
        f"<span style='font-size:0.78rem; color:#6B6580;'>Perfil: {perfil.upper()}</span>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sair", use_container_width=True):
        logout()
