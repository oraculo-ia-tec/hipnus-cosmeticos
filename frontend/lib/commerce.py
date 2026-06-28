"""
commerce.py — HIPNUS COSMÉTICOS
=====================================
Componentes de vitrine: catálogo, produto, carrinho, preço e checkout.

CHAVE DO CARRINHO: session_state["cart"] (dict {id: {id,name,price,qty}})
Nunca usar session_state["carrinho"] — era o nome legado que causava o bug.
"""

from __future__ import annotations
import streamlit as st
from . import tokens as T


# ── Helpers internos de carrinho ───────────────────────────────────────────────
def _cart() -> dict:
    """Retorna sempre session_state['cart'] como dict, inicializando se necessário."""
    if "cart" not in st.session_state or not isinstance(st.session_state["cart"], dict):
        st.session_state["cart"] = {}
    return st.session_state["cart"]


def _cart_as_list() -> list:
    """Converte o cart dict para lista de itens (para checkout_service e cart_view)."""
    return list(_cart().values())


# ── Formatação de preço ────────────────────────────────────────────────────────────────────
def brl(value) -> str:
    if value is None:
        return "—"
    s = f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


# ── Ícone de categoria ──────────────────────────────────────────────────────────────────────────
def category_icon(category: str | None) -> str:
    _CATEGORY_ICON: dict[str, str] = {
        "Mascara Liquida":        "💧",
        "Tratamento Obrigatorio": "✨",
        "Home Care":              "🏠",
        "Quimicas":               "🧪",
        "Mascaras Avulsas":       "🎥",
        "Mascaras Matizadoras":   "🎨",
        "Matizadores":            "🎨",
        "Linha Masculina":        "🧔",
        "Encapsulados":           "💊",
        "Diversos":               "🧴",
        "Geral":                  "🧴",
    }
    return _CATEGORY_ICON.get(category or "", "🧴")


# ── Card de produto ─────────────────────────────────────────────────────────────────────────────────
def product_card(p: dict, *, key_prefix: str = "cat", on_add=None) -> None:
    from . import ui
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
        <div class="price">{brl(price)}<small>{price_label}</small></div>
        <div class="floor">Piso parceiro: {brl(p.get('floor_price'))}</div>
    </div>
    """)
    if st.button("＋ Adicionar", key=f"{key_prefix}_add_{p['id']}", use_container_width=True):
        if on_add:
            on_add(p)
        else:
            ui.add_to_cart(p)  # grava em session_state["cart"]
        n = _cart().get(p["id"], {}).get("qty", 1)
        st.toast(f"🛒 {p['name'].title()} ×{n} no carrinho", icon="🛒")


# ── Linha do carrinho ──────────────────────────────────────────────────────────────────────────────────
def cart_row(item: dict, *, cart: dict) -> int | None:
    from . import ui
    c = st.columns([4, 1.4, 1.4, 1.6, 0.6])
    c[0].write(item["name"])
    c[1].write(brl(item["price"]))
    new_qty = c[2].number_input(
        "qtd", min_value=1, max_value=99, value=item["qty"],
        key=f"qty_{item['id']}", label_visibility="collapsed",
    )
    c[3].write(brl(item["price"] * item["qty"]))
    removed = c[4].button("🗑", key=f"rm_{item['id']}", help="Remover item")
    if removed:
        ui.remove_from_cart(item["id"])
        return 0
    return new_qty if new_qty != item["qty"] else None


# ── Bloco de total ─────────────────────────────────────────────────────────────────────────────────────
def cart_total_block(total: float, key_checkout: str = "go_checkout") -> bool:
    from . import ui
    st.markdown(f"### Total: {brl(total)}")
    checkout_clicked = st.button(
        "Finalizar compra 💳", type="primary",
        use_container_width=True, key=key_checkout,
    )
    if st.button("Limpar carrinho", use_container_width=True, key="clear_cart_btn"):
        ui.clear_cart()
        st.rerun()
    return checkout_clicked


# ── cart_view ──────────────────────────────────────────────────────────────────────────────────────────────
def cart_view(
    cart=None,
    on_remove=None,
    on_clear=None,
) -> None:
    """Renderiza a página completa do carrinho.
    Sempre lê de session_state['cart'] (dict) para garantir consistência.
    """
    from . import ui
    items = _cart_as_list()

    if not items:
        st.info("🛒 Carrinho vazio. Adicione produtos pelo Catálogo ou Loja do Parceiro.")
        if st.button("← Ver Catálogo", key="cart_back_catalog"):
            st.switch_page("pages/2_Catalogo.py")
        return

    total = sum(i.get("price", 0) * i.get("qty", 1) for i in items)
    st.markdown(f"**{len(items)} item(ns) no carrinho · Total: {brl(total)}**")
    st.divider()

    cols = st.columns([4, 1.4, 1.4, 1.6, 0.6])
    for h, label in zip(cols, ["Produto", "Preço", "Qtd", "Subtotal", ""]):
        h.markdown(f"**{label}**")

    changed = False
    for item in list(items):
        result = cart_row(item, cart=_cart())
        if result is not None:
            if result == 0:
                changed = True
            elif result != item["qty"]:
                _cart()[item["id"]]["qty"] = result
                changed = True
    if changed:
        st.rerun()

    st.divider()
    checkout_clicked = cart_total_block(total)
    if checkout_clicked:
        st.switch_page("pages/6_Checkout.py")


# ── checkout_view ────────────────────────────────────────────────────────────────────────────────────────────
def checkout_view(usuario: dict) -> None:
    """Renderiza o fluxo completo de Checkout com integração Asaas.
    Lê sempre de session_state['cart'] para garantir consistência com o catálogo.
    """
    try:
        from lib.checkout_service import processar_checkout
        cart = _cart_as_list()  # sempre lê session_state["cart"]

        if not cart:
            st.warning("🛒 Seu carrinho está vazio. Adicione produtos antes de finalizar.")
            if st.button("← Voltar ao Catálogo"):
                st.switch_page("pages/2_Catalogo.py")
            return

        total = sum(i.get("price", 0) * i.get("qty", 1) for i in cart)
        st.markdown(f"### Resumo do pedido · **{brl(total)}**")
        st.divider()
        for item in cart:
            st.markdown(
                f"- **{item.get('name','').title()}** · "
                f"{item.get('qty',1)}x · {brl(item.get('price',0) * item.get('qty',1))}"
            )
        st.divider()

        metodo = st.selectbox(
            "Forma de pagamento",
            ["PIX", "BOLETO", "CREDIT_CARD"],
            format_func=lambda m: {
                "PIX": "PIX 🟣",
                "BOLETO": "Boleto 📜",
                "CREDIT_CARD": "Cartão de Crédito 💳",
            }.get(m, m),
        )

        if st.button("Confirmar Pedido 💳", type="primary", use_container_width=True):
            with st.spinner("Processando pagamento..."):
                resultado = processar_checkout(
                    cart=cart,
                    usuario=usuario,
                    metodo=metodo,
                )
            if resultado.get("ok"):
                st.success("✅ Pedido realizado com sucesso!")
                st.balloons()
                if resultado.get("invoice_url"):
                    st.link_button("📎 Acessar fatura", resultado["invoice_url"])
                pedido_hist = {
                    "external_ref": resultado.get("external_ref", ""),
                    "payment_id":   resultado.get("payment_id", ""),
                    "status":       resultado.get("status", "PENDING"),
                    "totais":       {"total": total},
                }
                hist = st.session_state.get("historico_pedidos", [])
                hist.append(pedido_hist)
                st.session_state["historico_pedidos"] = hist
                st.session_state["cart"] = {}  # limpa com a chave correta
                st.rerun()
            else:
                st.error(f"❌ Erro no pagamento: {resultado.get('erro', 'Tente novamente.')}")
    except Exception as exc:
        st.error(f"❌ Erro no checkout: {exc}")
        st.info("💡 Verifique se ASAAS_API_KEY está configurada nas variáveis de ambiente.")
