"""
Cliente HTTP da API oficial do Asaas.

Encapsula as chamadas REST usadas pelo HIPNUS COSMÉTICOS:
- criação de SUBCONTAS (parceiros / wallets)            -> POST /accounts
- criação de CLIENTES                                   -> POST /customers
- criação de COBRANÇAS com SPLIT                         -> POST /payments
- consulta de cobranças                                 -> GET  /payments/{id}

Autenticação:
    Header `access_token: <ASAAS_API_KEY>` (chave da conta raiz Hipnus).

Ambientes:
    Sandbox:  https://api-sandbox.asaas.com/v3   (default em settings)
    Produção: https://api.asaas.com/v3

Observações importantes da API:
- A criação de subconta só é permitida para a conta raiz PJ (CNPJ).
- A resposta de POST /accounts devolve `apiKey` (apenas uma vez) e `walletId`.
- O `walletId` da subconta é usado no array `split` das cobranças.
"""
from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings


class AsaasError(RuntimeError):
    """Erro retornado pela API do Asaas (status >= 400)."""

    def __init__(self, status_code: int, payload: Any):
        self.status_code = status_code
        self.payload = payload
        super().__init__(f"Asaas API error {status_code}: {payload}")


class AsaasClient:
    """Wrapper fino sobre httpx para a API do Asaas."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or settings.ASAAS_API_KEY
        self.base_url = (base_url or settings.ASAAS_BASE_URL).rstrip("/")

    # ------------------------------------------------------------- internals
    @property
    def _headers(self) -> dict[str, str]:
        return {
            "access_token": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "HipnusCosmeticos/1.0",
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

    # ----------------------------------------------------------- subcontas
    def create_account(self, payload: dict) -> dict:
        """
        Cria uma subconta (parceiro) no Asaas.

        Retorna dict com, entre outros: `id`, `walletId`, `apiKey`.
        O `apiKey` é devolvido somente nesta resposta — deve ser persistido.
        """
        return self._request("POST", "/accounts", json=payload)

    # ----------------------------------------------------------- clientes
    def create_customer(self, payload: dict) -> dict:
        """Cria um cliente (pagador) no Asaas. Retorna dict com `id`."""
        return self._request("POST", "/customers", json=payload)

    # ----------------------------------------------------------- cobranças
    def create_payment(self, payload: dict) -> dict:
        """
        Cria uma cobrança. Para split, inclua em `payload['split']` uma lista
        de objetos `{"walletId": <wallet do parceiro>, "fixedValue"|"percentualValue": ...}`.
        """
        return self._request("POST", "/payments", json=payload)

    def get_payment(self, payment_id: str) -> dict:
        """Consulta o estado atual de uma cobrança."""
        return self._request("GET", f"/payments/{payment_id}")

    def get_pix_qrcode(self, payment_id: str) -> dict:
        """Retorna o QR Code Pix de uma cobrança (encodedImage, payload)."""
        return self._request("GET", f"/payments/{payment_id}/pixQrCode")
