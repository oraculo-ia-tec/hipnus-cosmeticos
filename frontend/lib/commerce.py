"""
commerce.py — HIPNUS COSMÉTICOS
=====================================
Componentes de vitrine: catálogo, produto, carrinho e preço.

Separa a responsabilidade de renderização dos dados de carrinho e produto,
que permanecem em ui.py (add_to_cart, cart_total, etc.) para compatibilidade.
"""

from __future__ import annotations
import streamlit as st
from . import tokens as T


# ───────────────────────────────────────── formatação de preço
def brl(value) -> str:
    """Formata número como moeda brasileira: R$ 1.234,56."""
    if value is None:
        return "—"
    s = f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


# ───────────────────────────────────────── ícone de categoria
_CATEGORY_ICON: dict[str, str] = {
    "Mascara Liquida":        "💧",
    "Tratamento Obrigatorio": "✨",
    "Home Care":              "🏠",
    "Quimicas":               "🧪",
    "Mascaras Avulsas":       "🎭",
    "Mascaras Matizadoras":   "🎨",
    "Matizadores":            "🎨",
    "Linha Masculina":        "🧔",
    "Encapsulados":           "💊",
    "Diversos":               "🧴",
    "Geral":                  "🧴",
}


def category_icon(category: str | None) -> str:
    """Retorna o emoji correspondente à categoria do produto."""
    return _CATEGORY_ICON.get(category or "", "🧴")


# ───────────────────────────────────────── card de produto
def product_card(p: dict, *, key_prefix: str = "cat", on_add=None) -> None:
    """Renderiza card de produto com preço, badges e botão de adicionar ao carrinho.

    Args:
        p:          Dicionário do produto. Campos esperados: id, name, line,
                    category, floor_price, suggested_retail_price, is_kit.
        key_prefix: Prefixo para a key do botão (evita conflito entre páginas).
        on_add:     Callback opcional chamado ao clicar em 'Adicionar'.
                    Se None, usa ui.add_to_cart internamente.

    Efeito colateral:
        Adiciona item ao st.session_state.cart e exibe st.toast().
    """
    from . import ui  # import local para evitar import circular

    price = p.get("suggested_retail_price") or p.get("floor_price")
    line  = p.get("line") or ""

    badges = ""
    if p.get("is_kit"):
        badges += '<span class="hip-badge kit">KIT</span>'
    if (p.get("line") or "").lower() == "ouro":
        badges += '<span class="hip-badge gold">Linha Ouro</span>'

    price_label = "sugerido" if p.get("suggested_retail_price") else "a partir de"

    st.html(f"""
    <div class="hip-card">
        <div class="hip-thumb">{category_icon(p.get('category'))}</div>
        <span class="line-tag">{line}&nbsp;</span>
        <div class="pname">{p['name'].title()}</div>
        <div class="badges">{badges}</div>
        <div class="price">
            {brl(price)}
            <small>{price_label}</small>
        </div>
        <div class="floor">Piso parceiro: {brl(p.get('floor_price'))}</div>
    </div>
    """)

    if st.button(
        "＋ Adicionar",
        key=f"{key_prefix}_add_{p['id']}",
        use_container_width=True,
    ):
        if on_add:
            on_add(p)
        else:
            ui.add_to_cart(p)
        st.toast(f"Adicionado: {p['name'].title()}", icon="🛒")


# ───────────────────────────────────────── linha de carrinho
def cart_row(item: dict, *, cart: dict) -> int | None:
    """Renderiza uma linha da tabela do carrinho com controles de quantidade e remoção.

    Args:
        item: Item do carrinho com campos: id, name, price, qty.
        cart: Referência ao dicionário st.session_state.cart.

    Returns:
        Nova quantidade se alterada pelo usuário, None se não houve mudança.
        Retorna 0 se o botão de remoção foi clicado.

    A página que chama este componente é responsável por aplicar st.rerun()
    quando o valor retornado for diferente de None.
    """
    from . import ui  # import local

    c = st.columns([4, 1.4, 1.4, 1.6, 0.6])
    c[0].write(item["name"])
    c[1].write(brl(item["price"]))

    new_qty = c[2].number_input(
        "qtd",
        min_value=1,
        max_value=99,
        value=item["qty"],
        key=f"qty_{item['id']}",
        label_visibility="collapsed",
    )

    c[3].write(brl(item["price"] * item["qty"]))

    removed = c[4].button("🗑", key=f"rm_{item['id']}", help="Remover item")
    if removed:
        ui.remove_from_cart(item["id"])
        return 0

    return new_qty if new_qty != item["qty"] else None


# ───────────────────────────────────────── resumo do total
def cart_total_block(total: float, key_checkout: str = "go_checkout") -> bool:
    """Renderiza o bloco de total e botões de ação do carrinho.

    Args:
        total:         Valor total calculado (use ui.cart_total()).
        key_checkout:  Key única do botão de finalizar compra.

    Returns:
        True se o botão 'Finalizar compra' foi clicado.
    """
    from . import ui  # import local

    st.markdown(f"### Total: {brl(total)}")
    checkout_clicked = st.button(
        "Finalizar compra 💳",
        type="primary",
        use_container_width=True,
        key=key_checkout,
    )
    if st.button("Limpar carrinho", use_container_width=True, key="clear_cart_btn"):
        ui.clear_cart()
        st.rerun()
    return checkout_clicked
