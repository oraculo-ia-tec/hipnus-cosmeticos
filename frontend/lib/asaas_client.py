"""
asaas_client.py — HIPNUS COSMÉTICOS
=====================================
Cliente HTTP standalone da API oficial do Asaas.

Versão autônoma para uso direto no Streamlit, SEM dependência do app/ (FastAPI).
Toda a lógica de chamada REST e split está aqui, pronta para importar
a partir de qualquer página do frontend.

Endpoints encapsulados:
  POST /accounts          → criar subconta do parceiro
  POST /customers         → criar/recuperar cliente (pagador)
  POST /payments          → criar cobrança com split automático
  GET  /payments/{id}     → consultar status da cobrança
  GET  /payments/{id}/pixQrCode → obter QR Code Pix

Autenticação: Header `access_token: <chave>` (conta raiz Hipnus).
Ambiente padrão: sandbox (https://api-sandbox.asaas.com/v3).

Uso:
    from lib.asaas_client import AsaasClient, AsaasService, AsaasError
    client  = AsaasClient(api_key="$aact_...", base_url="https://api-sandbox.asaas.com/v3")
    service = AsaasService(client=client)
"""
from __future__ import annotations

import os
from decimal import Decimal
from typing import Any

import httpx


# ─── Exceção ─────────────────────────────────────────────────────────────────
class AsaasError(RuntimeError):
    """Erro retornado pela API do Asaas (status >= 400)."""

    def __init__(self, status_code: int, payload: Any):
        self.status_code = status_code
        self.payload = payload
        super().__init__(f"Asaas API error {status_code}: {payload}")


# ─── Configuração ─────────────────────────────────────────────────────────────
def _read_secret(key: str, default: str = "") -> str:
    """Lê chave do Streamlit Secrets ou variável de ambiente."""
    try:
        import streamlit as st
        val = st.secrets.get(key)
        if val:
            return str(val)
    except Exception:
        pass
    return os.environ.get(key, default)


# ─── Cliente HTTP ─────────────────────────────────────────────────────────────
class AsaasClient:
    """
    Wrapper fino sobre httpx para a API REST do Asaas.

    Parâmetros:
        api_key  : Chave da conta raiz Hipnus (lê ASAAS_API_KEY se omitido).
        base_url : URL base da API (lê ASAAS_BASE_URL se omitido;
                   default: sandbox).
    """

    SANDBOX_URL    = "https://api-sandbox.asaas.com/v3"
    PRODUCTION_URL = "https://api.asaas.com/v3"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        self.api_key  = api_key  or _read_secret("ASAAS_API_KEY")
        self.base_url = (base_url or _read_secret("ASAAS_BASE_URL", self.SANDBOX_URL)).rstrip("/")

    # ── Internals ────────────────────────────────────────────────────────────
    @property
    def _headers(self) -> dict[str, str]:
        return {
            "access_token": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "HipnusCosmeticos/2.0-streamlit",
        }

    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=30.0) as client:
            resp = client.request(method, url, headers=self._headers, **kwargs)
        if resp.status_code >= 400:
            try:
                payload = resp.json()
            except Exception:
                payload = resp.text
            raise AsaasError(resp.status_code, payload)
        return resp.json() if resp.content else {}

    # ── Subcontas ────────────────────────────────────────────────────────────
    def create_account(self, payload: dict) -> dict:
        """
        Cria uma subconta (parceiro) no Asaas.
        Retorna dict com `id`, `walletId` e `apiKey` (persistir walletId!).
        """
        return self._request("POST", "/accounts", json=payload)

    # ── Clientes ─────────────────────────────────────────────────────────────
    def create_customer(self, payload: dict) -> dict:
        """Cria um cliente (pagador) no Asaas. Retorna dict com `id`."""
        return self._request("POST", "/customers", json=payload)

    # ── Cobranças ─────────────────────────────────────────────────────────────
    def create_payment(self, payload: dict) -> dict:
        """
        Cria uma cobrança. Para split automático, inclua `payload['split']`:
            [{"walletId": "wallet_xxx", "fixedValue": 12.50}]
        """
        return self._request("POST", "/payments", json=payload)

    def get_payment(self, payment_id: str) -> dict:
        """Consulta o estado atual de uma cobrança pelo ID."""
        return self._request("GET", f"/payments/{payment_id}")

    def get_pix_qrcode(self, payment_id: str) -> dict:
        """
        Retorna o QR Code Pix de uma cobrança.
        Campos úteis: `encodedImage` (base64), `payload` (copia-e-cola).
        """
        return self._request("GET", f"/payments/{payment_id}/pixQrCode")


# ─── Serviço de Split ─────────────────────────────────────────────────────────
class AsaasService:
    """
    Camada de negócio sobre o AsaasClient.

    Responsabilidades:
      - Provisionar subconta do parceiro (onboarding).
      - Calcular split (Hipnus x parceiro) com base no floor_price.
      - Criar cobrança com split automático.

    Modelo de split:
      total         = Σ(sale_price × qty)
      floor_total   = Σ(floor_price × qty)
      margem        = total − floor_total
      taxa plataform = margem × HIPNUS_PLATFORM_FEE_PERCENT / 100
      parceiro recebe = margem − taxa
      Hipnus retém    = floor_total + taxa  (conta raiz)
    """

    # Taxa padrão retida pela Hipnus sobre a margem do parceiro (%)
    DEFAULT_PLATFORM_FEE = Decimal("10")  # 10%

    def __init__(
        self,
        client: AsaasClient | None = None,
        platform_fee_percent: Decimal | None = None,
    ):
        self.client = client or AsaasClient()
        fee_env = _read_secret("HIPNUS_PLATFORM_FEE_PERCENT", "")
        self.platform_fee = (
            platform_fee_percent
            or (Decimal(fee_env) if fee_env else self.DEFAULT_PLATFORM_FEE)
        )

    # ── Onboarding ────────────────────────────────────────────────────────────
    def provision_partner_account(
        self,
        *,
        name: str,
        email: str,
        cpf_cnpj: str,
        phone: str | None = None,
        income_value: float,
        postal_code: str,
        address: str,
        address_number: str,
        province: str,
    ) -> dict:
        """
        Cria a subconta do parceiro no Asaas.
        Retorna payload com `id`, `walletId` e `apiKey` — persistir walletId!
        """
        payload = {
            "name":          name,
            "email":         email,
            "cpfCnpj":       cpf_cnpj,
            "mobilePhone":   phone,
            "incomeValue":   income_value,
            "address":       address,
            "addressNumber": address_number,
            "province":      province,
            "postalCode":    postal_code,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        return self.client.create_account(payload)

    # ── Cálculo do split ──────────────────────────────────────────────────────
    def compute_split(self, total: Decimal, floor_total: Decimal) -> dict:
        """
        Calcula a divisão do pagamento.

        Retorna:
            partner_amount  : valor repassado via split ao parceiro.
            hipnus_amount   : valor retido na conta raiz Hipnus.
            platform_fee    : taxa de plataforma cobrada sobre a margem.
        """
        margin  = max(Decimal("0"), total - floor_total)
        fee     = (margin * self.platform_fee / Decimal("100")).quantize(Decimal("0.01"))
        partner = (margin - fee).quantize(Decimal("0.01"))
        hipnus  = (total - partner).quantize(Decimal("0.01"))
        return {
            "partner_amount": partner,
            "hipnus_amount":  hipnus,
            "platform_fee":   fee,
        }

    # ── Cobrança com split ────────────────────────────────────────────────────
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
        Cria uma cobrança com split automático.

        O `partner_amount` é creditado na wallet do parceiro;
        o restante permanece na conta raiz Hipnus.

        billing_type: 'PIX' | 'BOLETO' | 'CREDIT_CARD'
        due_date    : 'YYYY-MM-DD'
        """
        payload = {
            "customer":         asaas_customer_id,
            "billingType":      billing_type,
            "value":            float(value),
            "dueDate":          due_date,
            "externalReference": external_reference,
            "description":      description,
            "split": [
                {
                    "walletId":   partner_wallet_id,
                    "fixedValue": float(partner_amount),
                }
            ],
        }
        return self.client.create_payment(payload)
