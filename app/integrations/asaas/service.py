"""
Serviço de orquestração Asaas — regras de negócio sobre o cliente HTTP.

Responsabilidades:
- Provisionar subconta de um parceiro (onboarding) e persistir wallet/apiKey.
- Montar cobranças com SPLIT correto a partir de um pedido.
- Calcular a divisão do split (Hipnus x parceiro) com base no piso e na taxa.

Modelo de split adotado:
    Para cada pedido pago:
      - valor total = soma(sale_price * qty)
      - valor do piso (Hipnus) = soma(floor_price * qty)
      - margem do parceiro = total - piso
      - taxa de plataforma Hipnus = margem * HIPNUS_PLATFORM_FEE_PERCENT
    O parceiro recebe via split: (margem - taxa de plataforma).
    A Hipnus retém o restante (piso + taxa) na conta raiz.

    No Asaas, o split é configurado repassando ao parceiro o `fixedValue`
    correspondente a (margem - taxa). O valor remanescente permanece na
    conta raiz Hipnus automaticamente.
"""
from __future__ import annotations

from decimal import Decimal

from app.core.config import settings
from app.integrations.asaas.client import AsaasClient


class AsaasService:
    def __init__(self, client: AsaasClient | None = None):
        self.client = client or AsaasClient()

    # --------------------------------------------------------- onboarding
    def provision_partner_account(
        self,
        *,
        name: str,
        email: str,
        cpf_cnpj: str,
        phone: str | None,
        income_value: float,
        postal_code: str,
        address: str,
        address_number: str,
        province: str,
    ) -> dict:
        """
        Cria a subconta do parceiro no Asaas.

        Parâmetros refletem os campos obrigatórios do endpoint /accounts
        (incomeValue, postalCode, etc.). Retorna o payload do Asaas contendo
        `id`, `walletId` e `apiKey` (persistir wallet/apiKey no Partner).
        """
        payload = {
            "name": name,
            "email": email,
            "cpfCnpj": cpf_cnpj,
            "mobilePhone": phone,
            "incomeValue": income_value,
            "address": address,
            "addressNumber": address_number,
            "province": province,
            "postalCode": postal_code,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        return self.client.create_account(payload)

    # --------------------------------------------------------- split calc
    @staticmethod
    def compute_split(total: Decimal, floor_total: Decimal) -> dict:
        """
        Calcula a divisão do pagamento.

        Retorna: {partner_amount, hipnus_amount, platform_fee}.
        - partner_amount: valor repassado ao parceiro via split.
        - platform_fee: taxa retida pela Hipnus sobre a margem.
        - hipnus_amount: total - partner_amount.
        """
        margin = max(Decimal("0"), total - floor_total)
        fee = (margin * Decimal(str(settings.HIPNUS_PLATFORM_FEE_PERCENT)) / Decimal("100"))
        partner_amount = (margin - fee).quantize(Decimal("0.01"))
        hipnus_amount = (total - partner_amount).quantize(Decimal("0.01"))
        return {
            "partner_amount": partner_amount,
            "hipnus_amount": hipnus_amount,
            "platform_fee": fee.quantize(Decimal("0.01")),
        }

    # --------------------------------------------------------- cobrança
    def create_charge_with_split(
        self,
        *,
        asaas_customer_id: str,
        billing_type: str,
        value: Decimal,
        partner_wallet_id: str,
        partner_amount: Decimal,
        due_date: str,
        external_reference: str,
        description: str,
    ) -> dict:
        """
        Cria uma cobrança com split para o parceiro.

        `partner_amount` é o valor (fixedValue) repassado à wallet do parceiro;
        o restante permanece na conta raiz Hipnus.
        """
        payload = {
            "customer": asaas_customer_id,
            "billingType": billing_type,           # PIX | CREDIT_CARD | BOLETO
            "value": float(value),
            "dueDate": due_date,                   # YYYY-MM-DD
            "externalReference": external_reference,
            "description": description,
            "split": [
                {
                    "walletId": partner_wallet_id,
                    "fixedValue": float(partner_amount),
                }
            ],
        }
        return self.client.create_payment(payload)
