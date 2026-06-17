"""
5_Checkout.py — HIPNUS COSMÉTICOS
====================================
Fluxo completo de pagamento via Asaas sem passar pelo FastAPI.

Etapas:
  1. Resumo do carrinho com valores e split.
  2. Dados do comprador (nome, CPF/CNPJ, e-mail, telefone).
  3. Escolha do método de pagamento (PIX | Boleto).
  4. Confirmação e chamada ao CheckoutService.
  5. Exibição do resultado: QR Code Pix ou link de boleto.
"""
import sys
import base64
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
from lib import ui
from lib.auth import require_auth, sidebar_user_info, sidebar_logout_button
from lib.checkout_service import CheckoutService, AsaasError
from lib import components

st.set_page_config(page_title="Checkout · HIPNUS", page_icon="💳", layout="centered")
ui.inject_theme()

require_auth()

# ─ Sidebar ───────────────────────────────────────────────────────────
ui.brand_header()
sidebar_user_info()
ui.sidebar_cart_summary()
sidebar_logout_button()

# ─ Cabeçalho ─────────────────────────────────────────────────────────
components.page_header(
    title="Finalizar Compra",
    subtitle="Revise seu pedido e escolha a forma de pagamento.",
    kicker="Checkout seguro",
)

cart = st.session_state.get("cart", {})

# ─ Carrinho vazio ────────────────────────────────────────────────────
if not cart:
    clicked = components.empty_state(
        icon="🛒",
        title="Seu carrinho está vazio",
        message="Adicione produtos antes de finalizar a compra.",
        action_label="Ir para o catálogo",
        action_key="checkout_empty_go_catalog",
    )
    if clicked:
        st.switch_page("pages/1_🛍️_Catálogo.py")
    st.stop()

# ─ Resumo do pedido ──────────────────────────────────────────────────
components.section_title("Resumo do pedido")

totais = CheckoutService.calcular_totais(cart)

col1, col2 = st.columns(2)
with col1:
    for item in cart.values():
        st.write(f"• {item['name']} × {item['qty']}  —  {ui.brl(item['price'] * item['qty'])}")
with col2:
    st.metric("Total", ui.brl(totais["total"]))
    st.caption(f"Parte Hipnus (piso): {ui.brl(totais['floor_total'])}")
    st.caption(f"Repasse ao parceiro: {ui.brl(totais['partner_amount'])}")

components.divider()

# ─ Formulário de dados + pagamento ───────────────────────────────────
components.section_title("Seus dados")

with st.form("form_checkout"):
    nome     = st.text_input("Nome completo *", placeholder="Ex: Maria da Silva")
    cpf_cnpj = st.text_input("CPF ou CNPJ * (somente números)", placeholder="00000000000")
    email    = st.text_input("E-mail *", placeholder="maria@email.com")
    fone     = st.text_input("Telefone (opcional)", placeholder="31999999999")

    components.divider()
    components.section_title("Forma de pagamento")

    metodo = st.radio(
        "Escolha o método:",
        options=["PIX", "BOLETO"],
        horizontal=True,
        captions=["QR Code instantâneo", "Vencimento em 3 dias"],
    )

    components.divider()
    confirmar = st.form_submit_button(
        "✅ Confirmar pagamento",
        type="primary",
        use_container_width=True,
    )

# ─ Processamento ─────────────────────────────────────────────────────
if confirmar:
    erros = []
    if not nome.strip():
        erros.append("Nome é obrigatório.")
    if not cpf_cnpj.strip() or not cpf_cnpj.strip().isdigit():
        erros.append("CPF/CNPJ inválido — informe apenas números.")
    if not email.strip() or "@" not in email:
        erros.append("E-mail inválido.")

    if erros:
        for e in erros:
            components.feedback_inline(e, kind="danger")
        st.stop()

    with st.spinner("Processando pagamento via Asaas..."):
        try:
            svc = CheckoutService()
            resultado = svc.processar(
                cart=cart,
                billing_type={"PIX": "PIX", "BOLETO": "BOLETO"}[metodo],
                cliente={
                    "name": nome.strip(),
                    "cpfCnpj": cpf_cnpj.strip(),
                    "email": email.strip(),
                    "phone": fone.strip(),
                },
                descricao="Pedido HIPNUS COSMÉTICOS",
            )

            components.feedback_inline(
                f"Pedido criado! Referência: {resultado['external_ref']}",
                kind="success",
            )
            st.caption(f"ID Asaas: `{resultado['payment_id']}` | Status: **{resultado['status']}**")

            if metodo == "PIX":
                components.section_title("Pague via PIX")
                if resultado["pix_qrcode"]:
                    img_bytes = base64.b64decode(resultado["pix_qrcode"])
                    st.image(img_bytes, caption="QR Code PIX", width=280)
                if resultado["pix_payload"]:
                    st.text_area("Copia e cola PIX:", value=resultado["pix_payload"], height=80)
                else:
                    with st.popover("ℹ️ QR Code em processamento", use_container_width=False):
                        st.markdown(
                            "O QR Code Pix estará disponível em instantes. "
                            "Use o link abaixo para acessar a cobrança diretamente."
                        )

            if resultado["invoice_url"]:
                st.link_button(
                    "🔗 Abrir link de pagamento",
                    url=resultado["invoice_url"],
                    use_container_width=True,
                )

            ui.clear_cart()
            st.session_state["ultimo_pedido"] = resultado

        except AsaasError as exc:
            components.feedback_inline(
                f"Erro na API Asaas ({exc.status_code}): {exc.payload}",
                kind="danger",
            )
        except Exception as exc:
            components.feedback_inline(f"Erro inesperado: {exc}", kind="danger")
