"""
checkout_service.py — HIPNUS COSMÉTICOS
=========================================
Camada de serviço de checkout para uso direto no Streamlit,
sem passar pelo FastAPI.

Responsabilidades:
  1. Registrar ou recuperar o cliente no Asaas pelo CPF/CNPJ.
  2. Calcular o split (Hipnus x parceiro) com base no floor_price.
  3. Criar a cobrança com split automático via AsaasClient.
  4. Retornar os dados de pagamento (link, QR Code Pix, etc.).

Hipóteses adotadas (Streamlit Cloud sem banco):
  - O wallet_id do parceiro é lido de st.secrets ou de uma variável
    de ambiente PARTNER_WALLET_ID (configurável por loja futuramente).
  - Sem banco de dados disponível, pedidos são registrados apenas no
    st.session_state (histórico de sessão). Quando o MySQL da Hostinger
    estiver configurado, basta chamar o repositório de Orders aqui.

Integrações ativas:
  - AsaasClient   (app/integrations/asaas/client.py)
  - AsaasService  (app/integrations/asaas/service.py)
"""
from __future__ import annotations

import sys
import os
from pathlib import Path
from decimal import Decimal
from datetime import date, timedelta

# Garante que o raiz do projeto está no path para importar app.*
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.integrations.asaas.client import AsaasClient, AsaasError  # noqa: E402
from app.integrations.asaas.service import AsaasService             # noqa: E402


# ------------------------------------------------------------------ helpers
def _get_env(key: str, default: str = "") -> str:
    """Lê segredo do Streamlit Secrets ou variável de ambiente."""
    try:
        import streamlit as st
        return st.secrets.get(key, os.environ.get(key, default))
    except Exception:
        return os.environ.get(key, default)


def _due_date(days: int = 3) -> str:
    """Retorna a data de vencimento no formato YYYY-MM-DD."""
    return (date.today() + timedelta(days=days)).isoformat()


def _build_external_ref(cart: dict) -> str:
    """Gera referência externa com base nos ids dos itens do carrinho."""
    ids = "-".join(str(v["id"]) for v in cart.values())
    return f"HIPNUS-{date.today().strftime('%Y%m%d')}-{ids}"


# ------------------------------------------------------------------ serviço
class CheckoutService:
    """
    Orquestra o fluxo completo de checkout para o Streamlit.

    Uso:
        svc = CheckoutService()
        resultado = svc.processar(
            cart=st.session_state["cart"],
            billing_type="PIX",
            cliente={"name": ..., "cpfCnpj": ..., "email": ..., "phone": ...},
            partner_wallet_id="wallet_xxx",   # opcional, lê de secrets se omitido
        )
    """

    def __init__(self):
        api_key = _get_env("ASAAS_API_KEY")
        base_url = _get_env("ASAAS_BASE_URL", "https://api-sandbox.asaas.com/v3")
        self.client = AsaasClient(api_key=api_key, base_url=base_url)
        self.service = AsaasService(client=self.client)

    # ------------------------------------------------ registro de cliente
    def registrar_cliente(self, nome: str, cpf_cnpj: str, email: str, fone: str = "") -> str:
        """
        Cria ou recupera o cliente no Asaas.

        Retorna o `id` do cliente Asaas (ex: 'cus_000001234').
        Em caso de CPF/CNPJ já cadastrado, o Asaas retorna o existente.

        Parâmetros:
            nome      : Nome completo do comprador.
            cpf_cnpj  : CPF ou CNPJ sem formatação.
            email     : E-mail do comprador.
            fone      : Telefone opcional.

        Retorna:
            str: ID do cliente no Asaas.

        Efeitos colaterais:
            Cria o cliente na API do Asaas se ainda não existir.
        """
        payload = {
            "name": nome,
            "cpfCnpj": cpf_cnpj,
            "email": email,
        }
        if fone:
            payload["mobilePhone"] = fone
        resultado = self.client.create_customer(payload)
        return resultado["id"]

    # ------------------------------------------------ cálculo do total
    @staticmethod
    def calcular_totais(cart: dict) -> dict:
        """
        Calcula total geral e total do piso (floor_price) a partir do carrinho.

        Parâmetros:
            cart: dict do st.session_state["cart"].
                  Cada item deve ter: price, floor_price (opcional), qty.

        Retorna:
            dict com total (Decimal), floor_total (Decimal),
            partner_amount (Decimal), platform_fee (Decimal).
        """
        total = Decimal("0")
        floor_total = Decimal("0")
        for item in cart.values():
            qty = Decimal(str(item.get("qty", 1)))
            price = Decimal(str(item.get("price", 0)))
            floor_price = Decimal(str(item.get("floor_price", item.get("price", 0))))
            total += price * qty
            floor_total += floor_price * qty

        split = AsaasService.compute_split(total, floor_total)
        return {
            "total": total,
            "floor_total": floor_total,
            "partner_amount": split["partner_amount"],
            "hipnus_amount": split["hipnus_amount"],
            "platform_fee": split["platform_fee"],
        }

    # ------------------------------------------------ fluxo principal
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
            cart              : Carrinho do st.session_state.
            billing_type      : 'PIX' | 'BOLETO' | 'CREDIT_CARD'.
            cliente           : {'name', 'cpfCnpj', 'email', 'phone' (opt)}.
            partner_wallet_id : walletId da subconta do parceiro (lê de
                                PARTNER_WALLET_ID nos secrets se omitido).
            descricao         : Descrição da cobrança.

        Retorna:
            dict com:
              - payment_id   : ID da cobrança no Asaas.
              - status       : Status inicial da cobrança.
              - invoice_url  : Link de pagamento (boleto/cartão).
              - pix_qrcode   : Base64 do QR Code (apenas billing_type=PIX).
              - pix_payload  : Copia-e-cola Pix (apenas billing_type=PIX).
              - totais       : dict com total, split, etc.
              - external_ref : Referência interna do pedido.

        Regras de negócio:
            - floor_price por item define quanto fica na Hipnus.
            - A margem (price - floor_price) é rateada entre parceiro e
              taxa de plataforma (HIPNUS_PLATFORM_FEE_PERCENT).
            - Sem parceiro configurado, todo o valor fica na conta raiz.

        Efeitos colaterais:
            - Cria cliente no Asaas.
            - Cria cobrança com split no Asaas.
        """
        wallet_id = partner_wallet_id or _get_env("PARTNER_WALLET_ID", "")
        totais = self.calcular_totais(cart)
        ext_ref = _build_external_ref(cart)

        # 1. Registra cliente
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
            # Sem parceiro configurado: cobrança simples sem split
            cobranca = self.client.create_payment({
                "customer": customer_id,
                "billingType": billing_type,
                "value": float(totais["total"]),
                "dueDate": _due_date(),
                "externalReference": ext_ref,
                "description": descricao,
            })

        payment_id = cobranca.get("id", "")
        resultado = {
            "payment_id": payment_id,
            "status": cobranca.get("status", ""),
            "invoice_url": cobranca.get("invoiceUrl") or cobranca.get("bankSlipUrl", ""),
            "pix_qrcode": "",
            "pix_payload": "",
            "totais": totais,
            "external_ref": ext_ref,
        }

        # 3. Para PIX, busca QR Code
        if billing_type == "PIX" and payment_id:
            try:
                pix = self.client.get_pix_qrcode(payment_id)
                resultado["pix_qrcode"] = pix.get("encodedImage", "")
                resultado["pix_payload"] = pix.get("payload", "")
            except AsaasError:
                pass  # QR Code pode demorar alguns segundos para ficar pronto

        return resultado
