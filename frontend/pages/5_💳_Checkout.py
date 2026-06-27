"""
5_Checkout.py — HIPNUS COSMÉTICOS
====================================
Fluxo completo de pagamento via Asaas, 100% no Streamlit.
Sem FastAPI. Sem httpx para backend interno.

Skill #3:
  - após criar a cobrança, envia confirmação por e-mail ao cliente
  - usa lib.email_service.send_order_confirmation_email
"""
import sys
import base64
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from lib import ui
from lib.auth import require_auth, sidebar_logo, sidebar_user_info, sidebar_logout_button
from lib.checkout_service import CheckoutService, AsaasError
from lib.email_service import send_order_confirmation_email
from lib import components

st.set_page_config(page_title="Checkout · HIPNUS", page_icon="💳", layout="centered")
ui.inject_theme()

require_auth()

sidebar_logo()
sidebar_user_info()
ui.sidebar_cart_summary()
sidebar_logout_button()

components.page_header(
    title="Finalizar Compra",
    subtitle="Revise seu pedido e escolha a forma de pagamento.",
    kicker="Checkout seguro · Asaas",
)

cart = st.session_state.get("cart", {})

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

components.section_title("Resumo do pedido")

svc    = CheckoutService()
totais = svc.calcular_totais(cart)

col1, col2 = st.columns([3, 2])
with col1:
    for item in cart.values():
        st.write(f"• **{item['name']}** × {item['qty']}  —  {ui.brl(item['price'] * item['qty'])}")
with col2:
    st.metric("Total", ui.brl(totais["total"]))
    st.caption(f"💜 Hipnus (piso + taxa): {ui.brl(totais['hipnus_amount'])}")
    st.caption(f"🤝 Repasse ao parceiro: {ui.brl(totais['partner_amount'])}")
    st.caption(f"📊 Taxa de plataforma: {ui.brl(totais['platform_fee'])}")

components.divider()
components.section_title("Seus dados")

with st.form("form_checkout"):
    col_a, col_b = st.columns(2)
    with col_a:
        nome     = st.text_input("Nome completo *", placeholder="Ex: Maria da Silva")
        cpf_cnpj = st.text_input("CPF ou CNPJ * (só números)", placeholder="00000000000")
    with col_b:
        email = st.text_input("E-mail *", placeholder="maria@email.com")
        fone  = st.text_input("Telefone (opcional)", placeholder="31999999999")

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

if confirmar:
    erros = []
    if not nome.strip():
        erros.append("Nome é obrigatório.")
    if not cpf_cnpj.strip() or not cpf_cnpj.strip().isdigit():
        erros.append("CPF/CNPJ inválido — informe apenas números.")
    if len(cpf_cnpj.strip()) not in (11, 14):
        erros.append("CPF deve ter 11 dígitos e CNPJ 14 dígitos.")
    if not email.strip() or "@" not in email:
        erros.append("E-mail inválido.")

    if erros:
        for e in erros:
            components.feedback_inline(e, kind="danger")
        st.stop()

    with st.spinner("Processando pagamento via Asaas..."):
        try:
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
                f"✅ Pedido criado! Referência: `{resultado['external_ref']}`",
                kind="success",
            )
            st.caption(f"ID Asaas: `{resultado['payment_id']}` | Status: **{resultado['status']}**")

            # Skill #3 — confirmação automática por e-mail
            itens_pedido = list(cart.values())
            ok_mail, msg_mail = send_order_confirmation_email(
                to_email=email.strip(),
                customer_name=nome.strip(),
                billing_type={"PIX": "PIX", "BOLETO": "BOLETO"}[metodo],
                resultado=resultado,
                itens=itens_pedido,
            )
            if ok_mail:
                st.success(f"📧 Confirmação enviada para {email.strip()}")
            else:
                st.warning(f"⚠️ Pedido criado, mas o e-mail de confirmação falhou: {msg_mail}")

            if metodo == "PIX":
                components.section_title("Pague via PIX")
                if resultado["pix_qrcode"]:
                    img_bytes = base64.b64decode(resultado["pix_qrcode"])
                    col_qr, _ = st.columns([1, 1])
                    with col_qr:
                        st.image(img_bytes, caption="QR Code PIX", width=280)
                if resultado["pix_payload"]:
                    st.text_area("Copia e cola PIX:", value=resultado["pix_payload"], height=80)
                elif not resultado["pix_qrcode"]:
                    st.info("⏳ QR Code em processamento pelo Asaas. Use o link abaixo para acessar a cobrança.")

            if resultado["invoice_url"]:
                st.link_button("🔗 Abrir link de pagamento", url=resultado["invoice_url"], use_container_width=True)

            ui.clear_cart()
            st.session_state["ultimo_pedido"] = resultado
            st.session_state.setdefault("historico_pedidos", []).insert(0, resultado)

        except AsaasError as exc:
            components.feedback_inline(f"❌ Erro na API Asaas ({exc.status_code}): {exc.payload}", kind="danger")
        except Exception as exc:
            components.feedback_inline(f"❌ Erro inesperado: {exc}", kind="danger")
