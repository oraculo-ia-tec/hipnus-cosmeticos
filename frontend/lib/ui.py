"""
ui.py — HIPNUS COSMÉTICOS
=====================================
Façade de compatibilidade: re-exporta tudo dos novos módulos do design system.

As páginas existentes continuam importando de lib.ui sem nenhuma alteração.
A migração acontece progressivamente: quando uma página for refatorada,
pode passar a importar diretamente de lib.theme, lib.components e lib.commerce.

Ordem de chamada na sidebar (por convenção):
  1. brand_header()               → logo Hipnus (topo)
  2. auth.sidebar_user_info()     → card do usuário (ACIMA do menu)
  3. [menu nativo Streamlit]      → renderizado automaticamente
  4. api_status_badge()           → status da API
  5. sidebar_cart_summary()       → resumo do carrinho
  6. auth.sidebar_logout_button() → SAIR (ABAIXO do menu)

REGRA DE NAVEGAÇÃO (Streamlit Cloud):
  Usar SEMPRE os wrappers de pages/ (raiz), nunca os caminhos com emoji.
  Mapa:
    Login          → "streamlit_app.py"
    Home           → "pages/1_Home.py"
    Catálogo       → "pages/2_Catalogo.py"
    Linhas         → "pages/3_Linhas.py"
    Loja Parceiro  → "pages/4_Loja_Parceiro.py"
    Carrinho       → "pages/5_Carrinho.py"
    Checkout       → "pages/6_Checkout.py"
    Convites       → "pages/7_Convites.py"
    Cadastro       → "pages/8_Cadastro_Parceiro.py"

NÃO adicionar lógica nova aqui — use os módulos especializados:
    lib/tokens.py      → tokens semânticos (cores, raio, sombra, fonte)
    lib/theme.py       → inject_theme(), inject_login_style()
    lib/components.py  → page_header, section_title, surface_card, empty_state...
    lib/commerce.py    → product_card, cart_row, cart_total_block, brl
"""
from __future__ import annotations

import streamlit as st

# ─ Re-exports de tema ──────────────────────────────────────────
from .theme import inject_theme, inject_login_style  # noqa: F401

# ─ Re-exports de tokens ───────────────────────────────────────
from . import tokens  # noqa: F401

# ─ Re-exports de componentes genéricos ──────────────────────────
from .components import (  # noqa: F401
    page_header,
    section_title,
    surface_card,
    empty_state,
    divider,
    feedback_inline,
    stat_card,
)

# ─ Re-exports de comércio ──────────────────────────────────────
from .commerce import (  # noqa: F401
    brl,
    category_icon,
    product_card,
    cart_row,
    cart_total_block,
)

# ─ Compatibilidade retroativa: COLORS e BRAND (usados em páginas antigas) ──
from .config import BRAND, COLORS, CURRENCY  # noqa: F401


# ─ Carrinho (mantido aqui para compatibilidade com todas as páginas) ──────
def _cart() -> dict:
    if "cart" not in st.session_state:
        st.session_state.cart = {}
    return st.session_state.cart


def add_to_cart(p: dict, qty: int = 1) -> None:
    """Adiciona um produto ao carrinho ou incrementa a quantidade.

    Args:
        p:   Dicionário do produto (id, name, suggested_retail_price, floor_price).
        qty: Quantidade a adicionar (padrão 1).
    """
    cart = _cart()
    pid   = p["id"]
    price = float(p.get("suggested_retail_price") or p.get("floor_price") or 0)
    if pid in cart:
        cart[pid]["qty"] += qty
    else:
        cart[pid] = {"id": pid, "name": p["name"].title(), "price": price, "qty": qty}


def cart_count() -> int:
    """Retorna o número total de itens (somando quantidades) no carrinho."""
    return sum(item["qty"] for item in _cart().values())


def cart_total() -> float:
    """Retorna o valor total do carrinho."""
    return sum(item["price"] * item["qty"] for item in _cart().values())


def remove_from_cart(pid: int) -> None:
    """Remove um produto do carrinho pelo seu ID."""
    _cart().pop(pid, None)


def clear_cart() -> None:
    """Esvazia o carrinho completamente."""
    st.session_state.cart = {}


def sidebar_cart_summary() -> None:
    """Resumo compacto do carrinho na sidebar.

    Exibe contagem de itens e total. Se houver itens, exibe link para o carrinho.
    Chamar após api_status_badge(), antes de sidebar_logout_button().
    """
    count = cart_count()
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"🛒 **Carrinho:** {count} item(ns)")
    if count:
        st.sidebar.markdown(f"**Total:** {brl(cart_total())}")
        st.sidebar.page_link("pages/5_Carrinho.py", label="Ver carrinho", icon="➡️")


def brand_header() -> None:
    """Renderiza a barra de marca no topo da sidebar.

    Deve ser a PRIMEIRA chamada de sidebar em cada página.
    Depende das classes CSS injetadas por inject_theme().
    """
    st.sidebar.html("""
    <div class="hip-brand">
        <div class="hip-logo">H</div>
        <div>
            <div class="name">HIPNUS</div>
            <div class="sub">Cosm&eacute;ticos</div>
        </div>
    </div>
    """)


def api_status_badge(online: bool) -> None:
    """Mostra na sidebar se a vitrine está conectada à API ou em modo demo.

    Args:
        online: True se a API respondeu com sucesso, False caso contrário.
    """
    if online:
        st.sidebar.success("API conectada", icon="🟢")
    else:
        st.sidebar.info("Modo demonstração (catálogo local)", icon="🟣")
