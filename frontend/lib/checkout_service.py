"""
checkout_service.py — HIPNUS COSMÉTICOS
=========================================
Camada de serviço de checkout para uso direto no Streamlit,
100% autônomo — SEM dependência do app/ (FastAPI).

Responsabilidades:
  1. Registrar ou recuperar o cliente no Asaas pelo CPF/CNPJ.
  2. Calcular o split (Hipnus × parceiro) com base no floor_price.
  3. Criar a cobrança com split automático via AsaasClient local.
  4. Retornar os dados de pagamento (link, QR Code Pix, etc.).
  5. Registrar o pedido no st.session_state (histórico da sessão).

Dependências internas:
  - lib.asaas_client  (AsaasClient, AsaasService, AsaasError)  ← 100% local

Sem FastAPI, sem app/, sem httpx para backend interno.
"""
from __future__ import annotations

import os
from decimal import Decimal
from datetime import date, timedelta

from lib.asaas_client import AsaasClient, AsaasService, AsaasError  # noqa: F401  (re-exporta AsaasError)


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _get_secret(key: str, default: str = "") -> str:
    """Lê do Streamlit Secrets ou variável de ambiente."""
    try:
        import streamlit as st
        val = st.secrets.get(key)
        if val:
            return str(val)
    except Exception:
        pass
    return os.environ.get(key, default)


def _due_date(days: int = 3) -> str:
    """Retorna a data de vencimento YYYY-MM-DD."""
    return (date.today() + timedelta(days=days)).isoformat()


def _build_external_ref(cart: dict) -> str:
    """Gera referência única a partir dos IDs dos itens do carrinho."""
    ids = "-".join(str(v["id"]) for v in cart.values())
    return f"HIPNUS-{date.today().strftime('%Y%m%d')}-{ids}"


# ─── Serviço ──────────────────────────────────────────────────────────────────
class CheckoutService:
    """
    Orquestra o fluxo completo de checkout diretamente no Streamlit.

    Uso básico:
        svc = CheckoutService()
        resultado = svc.processar(
            cart=st.session_state["cart"],
            billing_type="PIX",
            cliente={"name": ..., "cpfCnpj": ..., "email": ..., "phone": ...},
        )

    Resultado retornado:
        payment_id   : ID da cobrança no Asaas.
        status       : Status inicial ('PENDING', 'CONFIRMED', etc.).
        invoice_url  : Link de pagamento (boleto/cartão).
        pix_qrcode   : Base64 do QR Code (somente billing_type=PIX).
        pix_payload  : Copia-e-cola Pix (somente billing_type=PIX).
        totais       : dict com total, floor_total, partner_amount, etc.
        external_ref : Referência interna HIPNUS-YYYYMMDD-{ids}.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        _api_key  = api_key  or _get_secret("ASAAS_API_KEY")
        _base_url = base_url or _get_secret("ASAAS_BASE_URL", "https://api-sandbox.asaas.com/v3")
        self.client  = AsaasClient(api_key=_api_key, base_url=_base_url)
        self.service = AsaasService(client=self.client)

    # ── Cálculo de totais ─────────────────────────────────────────────────────
    def calcular_totais(self, cart: dict) -> dict:
        """
        Calcula total geral, total do piso e split a partir do carrinho.

        Cada item do cart deve conter: price, floor_price (opcional), qty.
        Se floor_price ausente, assume floor_price = price (margem zero).

        Retorna dict com:
            total          : Decimal — valor total da compra.
            floor_total    : Decimal — soma dos pisos (receita Hipnus mínima).
            partner_amount : Decimal — valor repassado ao parceiro via split.
            hipnus_amount  : Decimal — valor retido pela Hipnus.
            platform_fee   : Decimal — taxa de plataforma sobre a margem.
        """
        total       = Decimal("0")
        floor_total = Decimal("0")
        for item in cart.values():
            qty         = Decimal(str(item.get("qty", 1)))
            price       = Decimal(str(item.get("price", 0)))
            floor_price = Decimal(str(item.get("floor_price", item.get("price", 0))))
            total       += price * qty
            floor_total += floor_price * qty

        split = self.service.compute_split(total, floor_total)
        return {
            "total":          total,
            "floor_total":    floor_total,
            "partner_amount": split["partner_amount"],
            "hipnus_amount":  split["hipnus_amount"],
            "platform_fee":   split["platform_fee"],
        }

    # ── Registro de cliente ───────────────────────────────────────────────────
    def registrar_cliente(
        self,
        nome: str,
        cpf_cnpj: str,
        email: str,
        fone: str = "",
    ) -> str:
        """
        Cria ou recupera o cliente no Asaas.
        Retorna o `id` do cliente (ex: 'cus_000001234').
        O Asaas devolve o registro existente caso CPF/CNPJ já esteja cadastrado.
        """
        payload: dict = {
            "name":    nome,
            "cpfCnpj": cpf_cnpj,
            "email":   email,
        }
        if fone:
            payload["mobilePhone"] = fone
        resultado = self.client.create_customer(payload)
        return resultado["id"]

    # ── Fluxo principal ───────────────────────────────────────────────────────
    def processar(
        self,
        *,
        cart: dict,
        billing_type: str,
        cliente: dict,
        partner_wallet_id: str | None = None,
        descricao: str = "Pedido HIPNUS COSMÉTICOS",
    ) -> dict:
        """
        Executa o fluxo completo de checkout.

        Parâmetros:
            cart              : st.session_state["cart"].
            billing_type      : 'PIX' | 'BOLETO' | 'CREDIT_CARD'.
            cliente           : {'name', 'cpfCnpj', 'email', 'phone' (opt)}.
            partner_wallet_id : walletId da subconta do parceiro.
                                Se omitido, lê PARTNER_WALLET_ID nos Secrets.
                                Se vazio, cria cobrança simples sem split.
            descricao         : Descrição da cobrança no Asaas.

        Regras de negócio:
            - floor_price por item define quanto fica na Hipnus (mínimo).
            - Margem = price − floor_price → rateada entre parceiro e taxa.
            - Sem parceiro configurado → cobrança simples (100% Hipnus).

        Retorna:
            dict com payment_id, status, invoice_url, pix_qrcode,
            pix_payload, totais, external_ref.
        """
        wallet_id = partner_wallet_id or _get_secret("PARTNER_WALLET_ID", "")
        totais    = self.calcular_totais(cart)
        ext_ref   = _build_external_ref(cart)

        # 1. Registra cliente no Asaas
        customer_id = self.registrar_cliente(
            nome=cliente["name"],
            cpf_cnpj=cliente["cpfCnpj"],
            email=cliente["email"],
            fone=cliente.get("phone", ""),
        )

        # 2. Cria cobrança (com ou sem split)
        if wallet_id:
            cobranca = self.service.create_charge_with_split(
                asaas_customer_id=customer_id,
                billing_type=billing_type,
                value=totais["total"],
                partner_wallet_id=wallet_id,
                partner_amount=totais["partner_amount"],
                due_date=_due_date(),
                external_reference=ext_ref,
                description=descricao,
            )
        else:
            # Sem parceiro → cobrança simples (todo valor fica na conta raiz)
            cobranca = self.client.create_payment({
                "customer":         customer_id,
                "billingType":      billing_type,
                "value":            float(totais["total"]),
                "dueDate":          _due_date(),
                "externalReference": ext_ref,
                "description":      descricao,
            })

        payment_id = cobranca.get("id", "")
        resultado  = {
            "payment_id":  payment_id,
            "status":      cobranca.get("status", ""),
            "invoice_url": cobranca.get("invoiceUrl") or cobranca.get("bankSlipUrl", ""),
            "pix_qrcode":  "",
            "pix_payload": "",
            "totais":      totais,
            "external_ref": ext_ref,
        }

        # 3. Para PIX: tenta obter QR Code (pode demorar alguns segundos)
        if billing_type == "PIX" and payment_id:
            try:
                pix = self.client.get_pix_qrcode(payment_id)
                resultado["pix_qrcode"]  = pix.get("encodedImage", "")
                resultado["pix_payload"] = pix.get("payload", "")
            except AsaasError:
                pass  # QR Code fica disponível em instantes; link ainda funciona

        return resultado
