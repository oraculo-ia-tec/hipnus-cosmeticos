"""
ui.py — HIPNUS COSMÉTICOS
=====================================
Façade de compatibilidade: re-exporta tudo dos novos módulos do design system.

As páginas existentes continuam importando de lib.ui sem nenhuma alteração.
A migração acontece progressivamente: quando uma página for refatorada,
pode passar a importar diretamente de lib.theme, lib.components e lib.commerce.

Ordem de chamada na sidebar (por convenção):
  1. auth.sidebar_logo()          → logo Hipnus (TOPO)
  2. auth.sidebar_user_info()     → card do usuário (ACIMA do menu)
  3. [menu nativo Streamlit]      → renderizado automaticamente
  4. auth.sidebar_logout_button() → SAIR (logo abaixo do menu — order CSS)

No corpo da página (chamar logo após inject_theme):
  5. ui.floating_cart_expander()  → carrinho flutuante no canto superior direito

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


def floating_cart_expander() -> None:
    """Carrinho flutuante fixo no canto superior direito da tela.

    Renderiza um expander 🛒 posicionado via CSS position:fixed no topo direito.
    Ao clicar, o usuário visualiza todos os itens, quantidades, preços e total.
    Inclui link direto para a página de carrinho completo.

    Chamar logo após inject_theme() em todas as páginas autenticadas,
    ANTES do conteúdo principal.

    Efeitos colaterais:
        - Lê st.session_state.cart (não modifica)
        - Injeta CSS via st.html() para o posicionamento fixo
    """
    count = cart_count()
    total = cart_total()
    cart  = _cart()

    # CSS para fixar o expander no canto superior direito
    st.html("""
    <style>
    /* ── Carrinho flutuante ── */
    div[data-testid="stExpander"].hip-cart-float {
        position: fixed !important;
        top: 56px !important;
        right: 18px !important;
        z-index: 9999 !important;
        width: 300px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,.18) !important;
        border-radius: 14px !important;
        background: #fff !important;
        border: 1px solid #e5e7eb !important;
    }
    /* Hack: o Streamlit não suporta classe direta no expander,
       então marcamos via wrapper de container */
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stExpander"].hip-cart-float) {
        position: fixed !important;
        top: 56px !important;
        right: 18px !important;
        z-index: 9999 !important;
        width: 300px !important;
    }
    /* Fallback universal: último expander dentro do bloco fixed-cart-wrap */
    #fixed-cart-wrap {
        position: fixed;
        top: 56px;
        right: 18px;
        z-index: 9999;
        width: 300px;
    }
    </style>
    <div id="fixed-cart-wrap"></div>
    """)

    # Âncora HTML que precede o expander para o JS posicionar
    st.html("""
    <script>
    (function() {
        function moveCart() {
            var anchor = document.getElementById('fixed-cart-wrap');
            if (!anchor) return;
            // Encontra o próximo expander irmão no DOM
            var parent = anchor.closest('[data-testid="stVerticalBlock"]');
            if (!parent) return;
            var expanders = parent.querySelectorAll('[data-testid="stExpander"]');
            expanders.forEach(function(el) {
                if (el.querySelector('.hip-cart-label')) {
                    anchor.appendChild(el);
                }
            });
        }
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', moveCart);
        } else {
            setTimeout(moveCart, 200);
        }
    })();
    </script>
    """)

    label = f"🛒 {count} item{'ns' if count != 1 else ''}  ·  {brl(total)}" if count else "🛒 Carrinho vazio"

    with st.expander(label, expanded=False):
        st.markdown('<span class="hip-cart-label" style="display:none"></span>', unsafe_allow_html=True)
        if not cart:
            st.caption("Nenhum produto adicionado ainda.")
        else:
            for item in cart.values():
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"**{item['name']}**  \n`x{item['qty']}`")
                c2.markdown(f"`{brl(item['price'] * item['qty'])}`")
            st.markdown("---")
            st.markdown(f"**Total: {brl(total)}**")
            st.page_link("pages/5_Carrinho.py", label="Ver carrinho completo →", icon="🛒")


def sidebar_cart_summary() -> None:
    """[LEGADO] Mantido para compatibilidade. Use floating_cart_expander().

    Exibe contagem de itens e total na sidebar.
    Substituído pelo floating_cart_expander() no canto superior direito.
    Ainda funciona mas não é mais chamado nas páginas padrão.
    """
    count = cart_count()
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"🛒 **Carrinho:** {count} item(ns)")
    if count:
        st.sidebar.markdown(f"**Total:** {brl(cart_total())}")
        st.sidebar.page_link("pages/5_Carrinho.py", label="Ver carrinho", icon="➡️")


def brand_header() -> None:
    """[LEGADO] Compatibilidade — chama a nova sidebar_logo() de auth.py.

    Mantido para não quebrar páginas que ainda usam ui.brand_header().
    Novas páginas devem usar auth.sidebar_logo() diretamente.
    """
    from .auth import sidebar_logo  # evita import circular no topo
    sidebar_logo()


def api_status_badge(online: bool) -> None:
    """Mostra na sidebar se a vitrine está conectada à API.

    Exibe badge verde apenas quando a API está online.
    Quando offline, não exibe nada (modo demonstração suprimido da sidebar).

    Args:
        online: True se a API respondeu com sucesso, False caso contrário.
    """
    if online:
        st.sidebar.success("API conectada", icon="🟢")
