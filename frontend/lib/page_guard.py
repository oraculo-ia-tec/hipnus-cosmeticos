"""
page_guard.py — HIPNUS COSMÉTICOS
=====================================
Controle de acesso por página baseado no perfil do usuário.

Mapa de permissões:
  super_admin  → acessa tudo
  admin        → acessa tudo exceto usuários internos
  b2b          → loja, catálogo, carrinho, checkout, convites
  b2c          → catálogo, carrinho, checkout
  demo         → somente catálogo e linhas (somente leitura)

Uso:
    from lib.page_guard import guard
    guard()  # bloqueia se sem permissão; redireciona para login se não autenticado
"""
from __future__ import annotations
import streamlit as st

# Mapa: chave do arquivo (sem prefixo numérico e emoji) → perfis permitidos
PAGE_PERMISSIONS: dict[str, list[str]] = {
    # Admin
    "dashboard":         ["super_admin", "admin"],
    "usuarios":          ["super_admin"],
    "configuracao":      ["super_admin", "admin"],
    "convites":          ["super_admin", "admin", "b2b"],
    # Loja
    "loja_do_parceiro":  ["super_admin", "admin", "b2b"],
    "loja_parceiro":     ["super_admin", "admin", "b2b"],
    "checkout":          ["super_admin", "admin", "b2b", "b2c"],
    "carrinho":          ["super_admin", "admin", "b2b", "b2c"],
    # Conteúdo aberto a autenticados
    "home":              ["super_admin", "admin", "b2b", "b2c", "demo"],
    "catalogo":          ["super_admin", "admin", "b2b", "b2c", "demo"],
    "linhas":            ["super_admin", "admin", "b2b", "b2c", "demo"],
    "ia_consultora":     ["super_admin", "admin", "b2b", "b2c"],
    "cadastro_parceiro": ["super_admin", "admin", "b2b", "b2c", "demo"],
}

_ROLE_LABELS = {
    "super_admin": "⭐ Super Admin",
    "admin":       "🛡️ Admin",
    "b2b":         "🎤 Profissional",
    "b2c":         "👤 Cliente",
    "demo":        "👀 Demo",
}


def _page_key(filename: str) -> str:
    """Extrai chave normalizada do nome do arquivo.
    Ex: '4_\U0001f6d2_Carrinho.py' → 'carrinho'
    """
    import re
    stem = filename.replace(".py", "").lower()
    # remove prefixo numérico
    stem = re.sub(r"^\d+_", "", stem)
    # remove emojis e caracteres não-ascii
    stem = stem.encode("ascii", "ignore").decode()
    stem = stem.strip("_").strip()
    return stem


def guard(page_key: str | None = None) -> dict:
    """
    Verifica autenticação e permissão de acesso.
    - Redireciona para login se não autenticado.
    - Exibe erro 403 e para o script se sem permissão.
    - Retorna o dict do usuário atual se permitido.

    page_key: chave manual (ex: 'dashboard'). Se omitida, detecta automaticamente.
    """
    import traceback
    from pathlib import Path

    if not st.session_state.get("autenticado"):
        st.switch_page("streamlit_app.py")

    usuario = {
        "login":        st.session_state.get("usuario", ""),
        "perfil":       st.session_state.get("perfil", "demo"),
        "nome":         st.session_state.get("nome", "Visitante"),
        "display_name": st.session_state.get("display_name", ""),
        "email":        st.session_state.get("email", ""),
        "token":        st.session_state.get("token", None),
        "via_api":      st.session_state.get("via_api", False),
        "avatar_b64":   st.session_state.get("avatar_b64", None),
    }
    perfil = usuario["perfil"]

    # Detecta chave da página automaticamente pelo call stack
    if not page_key:
        for frame in traceback.extract_stack():
            fname = Path(frame.filename).name
            if fname not in ("page_guard.py", "<string>", "streamlit_app.py"):
                page_key = _page_key(fname)
                break
        page_key = page_key or "home"

    permitidos = PAGE_PERMISSIONS.get(page_key)
    if permitidos and perfil not in permitidos:
        st.html(f"""
        <div style="text-align:center;padding:48px 24px;">
          <div style="font-size:4rem;margin-bottom:16px;">🚫</div>
          <div style="font-weight:800;font-size:1.4rem;color:#fff;margin-bottom:8px;">
            Acesso não permitido
          </div>
          <div style="color:rgba(255,255,255,.6);font-size:.95rem;margin-bottom:20px;">
            Seu perfil <strong>{_ROLE_LABELS.get(perfil, perfil)}</strong>
            não tem permissão para acessar esta página.
          </div>
          <a href="/" style="background:rgba(124,58,237,.4);color:#e9d5ff;
            padding:10px 28px;border-radius:999px;text-decoration:none;
            font-weight:600;font-size:.9rem;border:1px solid rgba(185,131,255,.3);">
            ← Voltar ao início
          </a>
        </div>
        """)
        st.stop()

    return usuario
