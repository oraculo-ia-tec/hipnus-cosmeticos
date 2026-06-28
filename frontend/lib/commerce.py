"""
commerce.py - HIPNUS COSMETICOS
=====================================
Componentes de vitrine: catalogo, produto, carrinho, preco e checkout.

CHAVE DO CARRINHO: session_state["cart"] (dict {id: {id,name,price,qty}})
"""

from __future__ import annotations
import re
import streamlit as st
from . import tokens as T

# Streamlit switch_page aceita apenas paths relativos a raiz do projeto
# e apenas arquivos dentro de pages/ (sem emoji no nome)
_CHECKOUT_PAGE  = "pages/6_Checkout.py"
_CATALOGO_PAGE  = "pages/2_Catalogo.py"


def _cart() -> dict:
    if "cart" not in st.session_state or not isinstance(st.session_state["cart"], dict):
        st.session_state["cart"] = {}
    return st.session_state["cart"]


def _cart_as_list() -> list:
    return list(_cart().values())


def brl(value) -> str:
    if value is None:
        return "-"
    s = f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return "R$ " + s


def category_icon(category: str | None) -> str:
    _MAP: dict[str, str] = {
        "Mascara Liquida":        "Liq",
        "Tratamento Obrigatorio": "Trat",
        "Home Care":              "HC",
        "Quimicas":               "Qui",
        "Mascaras Avulsas":       "Mas",
        "Mascaras Matizadoras":   "Mat",
        "Matizadores":            "Mat",
        "Linha Masculina":        "Masc",
        "Encapsulados":           "Enc",
        "Diversos":               "Div",
        "Geral":                  "Ger",
    }
    return _MAP.get(category or "", "Prod")


def _limpar_doc(doc: str) -> str:
    return re.sub(r"[^\d]", "", doc.strip())

def _validar_cpf(cpf: str) -> bool:
    c = _limpar_doc(cpf)
    if len(c) != 11 or c == c[0] * 11:
        return False
    for i in range(9, 11):
        soma = sum(int(c[j]) * (i + 1 - j) for j in range(i))
        if (soma * 10 % 11) % 10 != int(c[i]):
            return False
    return True

def _validar_cnpj(cnpj: str) -> bool:
    c = _limpar_doc(cnpj)
    if len(c) != 14 or c == c[0] * 14:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6] + pesos1
    for pesos, idx in [(pesos1, 12), (pesos2, 13)]:
        soma = sum(int(c[i]) * pesos[i] for i in range(idx))
        digito = 0 if soma % 11 < 2 else 11 - soma % 11
        if digito != int(c[idx]):
            return False
    return True

def _validar_documento(doc: str) -> tuple[bool, str]:
    c = _limpar_doc(doc)
    if len(c) == 11:
        return _validar_cpf(c), c
    if len(c) == 14:
        return _validar_cnpj(c), c
    return False, c


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
    cat_icon = category_icon(p.get("category"))
    name_title = p["name"].title()
    price_brl = brl(price)
    floor_brl = brl(p.get("floor_price"))
    st.html(f"""
    <div class="hip-card">
        <div class="hip-thumb">{cat_icon}</div>
        <span class="line-tag">{line}&nbsp;</span>
        <div class="pname">{name_title}</div>
        <div class="badges">{badges}</div>
        <div class="price">{price_brl}<small>{price_label}</small></div>
        <div class="floor">Piso parceiro: {floor_brl}</div>
    </div>
    """)
    if st.button("+ Adicionar", key=f"{key_prefix}_add_{p['id']}", use_container_width=True):
        if on_add:
            on_add(p)
        else:
            ui.add_to_cart(p)
        n = _cart().get(p["id"], {}).get("qty", 1)
        st.toast(f"Produto {name_title} x{n} no carrinho")


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
    removed = c[4].button("X", key=f"rm_{item['id']}", help="Remover item")
    if removed:
        ui.remove_from_cart(item["id"])
        return 0
    return new_qty if new_qty != item["qty"] else None


def cart_total_block(total: float, key_checkout: str = "go_checkout") -> bool:
    from . import ui
    st.markdown(f"### Total: {brl(total)}")
    checkout_clicked = st.button(
        "Finalizar compra", type="primary",
        use_container_width=True, key=key_checkout,
    )
    if st.button("Limpar carrinho", use_container_width=True, key="clear_cart_btn"):
        ui.clear_cart()
        st.rerun()
    return checkout_clicked


def cart_view(cart=None, on_remove=None, on_clear=None) -> None:
    from . import ui
    items = _cart_as_list()

    if not items:
        st.info("Carrinho vazio. Adicione produtos pelo Catalogo ou Loja do Parceiro.")
        if st.button("Ver Catalogo", key="cart_back_catalog"):
            st.switch_page(_CATALOGO_PAGE)
        return

    total = sum(i.get("price", 0) * i.get("qty", 1) for i in items)
    st.markdown(f"**{len(items)} item(ns) no carrinho - Total: {brl(total)}**")
    st.divider()

    cols = st.columns([4, 1.4, 1.4, 1.6, 0.6])
    for h, label in zip(cols, ["Produto", "Preco", "Qtd", "Subtotal", ""]):
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
    if cart_total_block(total):
        st.switch_page(_CHECKOUT_PAGE)


def checkout_view(usuario: dict) -> None:
    """
    Fluxo de Checkout em 2 etapas:
      Etapa 1 - Dados do comprador (CPF/CNPJ obrigatorio + validacao)
      Etapa 2 - Forma de pagamento (PIX ou Cartao de Credito) + confirmar
    """
    try:
        from lib.checkout_service import processar_checkout
        from lib.user_db import atualizar_cpf_phone

        cart = _cart_as_list()
        if not cart:
            st.warning("Seu carrinho esta vazio. Adicione produtos antes de finalizar.")
            if st.button("Voltar ao Catalogo"):
                st.switch_page(_CATALOGO_PAGE)
            return

        total = sum(i.get("price", 0) * i.get("qty", 1) for i in cart)

        with st.expander("Resumo do pedido - " + brl(total), expanded=True):
            for item in cart:
                name_t = item.get("name", "").title()
                qty    = item.get("qty", 1)
                subtot = brl(item.get("price", 0) * qty)
                st.markdown(f"- **{name_t}** - {qty}x - {subtot}")
            st.markdown(f"**Total: {brl(total)}**")

        st.divider()
        st.markdown("### Etapa 1 - Dados do comprador")
        st.caption("Preencha os dados abaixo para emissao da cobranca. CPF ou CNPJ e obrigatorio.")

        _saved = st.session_state.get("checkout_dados", {})
        if not isinstance(_saved, dict):
            _saved = {}

        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input(
                "Nome completo *",
                value=_saved.get("nome") or usuario.get("name") or usuario.get("username", ""),
                placeholder="Ex: Maria Silva",
                key="co_nome",
            )
            email = st.text_input(
                "E-mail *",
                value=_saved.get("email") or usuario.get("email", ""),
                placeholder="exemplo@email.com",
                key="co_email",
            )
        with col2:
            cpf_cnpj_raw = st.text_input(
                "CPF ou CNPJ *",
                value=_saved.get("cpf_cnpj") or usuario.get("cpf_cnpj") or usuario.get("cpf", ""),
                placeholder="000.000.000-00 ou 00.000.000/0001-00",
                help="Digite somente numeros ou com pontuacao padrao.",
                key="co_cpf_cnpj",
            )
            telefone = st.text_input(
                "Telefone (WhatsApp)",
                value=_saved.get("telefone") or usuario.get("phone") or usuario.get("telefone", ""),
                placeholder="(11) 99999-9999",
                key="co_telefone",
            )

        doc_ok, doc_limpo = _validar_documento(cpf_cnpj_raw)
        if cpf_cnpj_raw.strip() and not doc_ok:
            st.error("CPF ou CNPJ invalido. Verifique e tente novamente.")
        elif cpf_cnpj_raw.strip() and doc_ok:
            tipo_doc = "CPF" if len(doc_limpo) == 11 else "CNPJ"
            st.success(f"{tipo_doc} valido")

        dados_ok = nome.strip() and email.strip() and "@" in email and doc_ok

        if not dados_ok:
            st.info("Preencha todos os campos obrigatorios (*) corretamente para continuar.")
            return

        st.session_state["checkout_dados"] = {
            "nome":     nome.strip(),
            "email":    email.strip(),
            "cpf_cnpj": doc_limpo,
            "telefone": telefone.strip(),
        }

        usuario_state = st.session_state.get("usuario")
        if isinstance(usuario_state, dict):
            usuario_state["cpf_cnpj"] = doc_limpo
            usuario_state["phone"]    = telefone.strip()

        st.divider()
        st.markdown("### Etapa 2 - Forma de pagamento")

        metodo = st.selectbox(
            "Selecione como deseja pagar",
            ["PIX", "CREDIT_CARD"],
            format_func=lambda m: {
                "PIX":         "PIX - pagamento instantaneo",
                "CREDIT_CARD": "Cartao de Credito",
            }.get(m, m),
            key="co_metodo",
        )

        if metodo == "PIX":
            st.info("Um QR Code PIX sera gerado apos a confirmacao. Voce tera 3 dias para pagar.")
        else:
            st.info("Voce sera direcionado ao link de pagamento seguro do Asaas.")

        st.markdown(f"#### Total a pagar: {brl(total)}")

        if st.button("Confirmar Pedido", type="primary", use_container_width=True, key="co_confirmar"):
            with st.spinner("Processando pagamento..."):
                dados = st.session_state["checkout_dados"]
                usuario_checkout = {
                    **(usuario if isinstance(usuario, dict) else {}),
                    "name":     dados["nome"],
                    "email":    dados["email"],
                    "cpf_cnpj": dados["cpf_cnpj"],
                    "phone":    dados["telefone"],
                }
                resultado = processar_checkout(
                    cart=cart,
                    usuario=usuario_checkout,
                    metodo=metodo,
                )

            if resultado.get("ok"):
                email_usuario = dados.get("email") or usuario.get("email", "")
                if email_usuario:
                    atualizar_cpf_phone(
                        email=email_usuario,
                        cpf_cnpj=dados["cpf_cnpj"],
                        phone=dados["telefone"],
                    )

                st.success("Pedido realizado com sucesso!")
                st.balloons()

                if resultado.get("pix_qrcode"):
                    st.markdown("#### QR Code PIX")
                    import base64
                    st.image(base64.b64decode(resultado["pix_qrcode"]), caption="Escaneie para pagar", width=280)

                if resultado.get("pix_payload"):
                    st.text_area("Pix Copia e Cola", resultado["pix_payload"], height=80)

                if resultado.get("invoice_url"):
                    st.link_button("Acessar fatura / link de pagamento", resultado["invoice_url"])

                hist = st.session_state.get("historico_pedidos", [])
                hist.append({
                    "external_ref": resultado.get("external_ref", ""),
                    "payment_id":   resultado.get("payment_id", ""),
                    "status":       resultado.get("status", "PENDING"),
                    "metodo":       metodo,
                    "totais":       {"total": total},
                })
                st.session_state["historico_pedidos"] = hist
                st.session_state["cart"] = {}
                st.session_state.pop("checkout_dados", None)
            else:
                erro_msg = resultado.get("erro", "Tente novamente.")
                st.error(f"Erro no pagamento: {erro_msg}")

    except Exception as exc:
        st.error(f"Erro no checkout: {exc}")
        st.info("Verifique se ASAAS_API_KEY esta configurada nas variaveis de ambiente.")
