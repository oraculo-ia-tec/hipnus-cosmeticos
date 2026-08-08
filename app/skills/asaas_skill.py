"""
asaas_skill.py — TÁLYA COSMÉTICOS
=====================================
Skill de Integração Asaas: módulo compartilhado entre backend e frontend.

Encapsula TODAS as chamadas REST ao Asaas e a lógica de split:
  POST /accounts          → criar subconta do parceiro
  POST /customers         → criar/recuperar cliente (pagador)
  POST /payments          → criar cobrança com split automático
  GET  /payments/{id}     → consultar status da cobrança
  GET  /payments/{id}/pixQrCode → obter QR Code Pix
  GET  /payments          → listar cobranças com filtros

Autenticação: Header `access_token: <chave>` (conta raiz Tálya).

Resolução de credenciais (em ordem de prioridade):
  1. Argumento explícito no construtor
  2. st.secrets["asaas"]["ASAAS_API_KEY"]  (Streamlit Cloud)
  3. st.secrets["ASAAS_API_KEY"]           (raiz do secrets.toml)
  4. os.environ["ASAAS_API_KEY"]
  5. settings.asaas_api_key                (Pydantic Settings / .env)

Substitui:
  - app/integrations/asaas/client.py   → AsaasClient
  - app/integrations/asaas/service.py  → AsaasService
  - frontend/lib/asaas_client.py       → AsaasClient + AsaasService (frontend)

Uso no backend:
    from app.skills.asaas_skill import AsaasClient, AsaasService, AsaasError

Uso no frontend (Streamlit):
    from app.skills.asaas_skill import AsaasClient, AsaasService, AsaasError
"""
from __future__ import annotations

import os
from decimal import Decimal
from typing import Any

import httpx


# ─── Resolução de credenciais ────────────────────────────────────────────────

def _resolve_secret(key: str, default: str = "") -> str:
    """
    Lê uma credencial com fallback em 4 camadas:
      1. st.secrets["asaas"][key]  — seção [asaas] no secrets.toml
      2. st.secrets[key]           — raiz do secrets.toml
      3. os.environ[key]
      4. settings.<key.lower()>
    """
    # Streamlit secrets
    try:
        import streamlit as st
        try:
            val = st.secrets["asaas"][key]
            if val is not None and str(val).strip():
                return str(val).strip()
        except Exception:
            pass
        try:
            val = st.secrets[key]
            if val is not None and str(val).strip():
                return str(val).strip()
        except Exception:
            pass
    except Exception:
        pass

    # Variável de ambiente
    val = os.environ.get(key, "")
    if val:
        return val.strip()

    # Pydantic settings
    try:
        from app.core.config import settings
        attr = key.lower()
        val = str(getattr(settings, attr, ""))
        if val:
            return val.strip()
    except Exception:
        pass

    return default


# ─── Exceção ─────────────────────────────────────────────────────────────────

class AsaasError(RuntimeError):
    """Erro retornado pela API do Asaas (status >= 400)."""

    def __init__(self, status_code: int, payload: Any):
        self.status_code = status_code
        self.payload = payload
        super().__init__(f"Asaas API error {status_code}: {payload}")


# ─── Cliente HTTP ─────────────────────────────────────────────────────────────

class AsaasClient:
    """
    Wrapper fino sobre httpx para a API REST do Asaas.

    Funciona sem dependência do Pydantic Settings — resolve credenciais
    via st.secrets, os.environ ou settings, nessa ordem.
    """

    SANDBOX_URL    = "https://api-sandbox.asaas.com/v3"
    PRODUCTION_URL = "https://api.asaas.com/v3"

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key  = api_key  or _resolve_secret("ASAAS_API_KEY")
        self.base_url = (
            base_url or _resolve_secret("ASAAS_BASE_URL", self.SANDBOX_URL)
        ).rstrip("/")

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "access_token": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "TalyaCosmeticos/2.0",
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

    # ── Subcontas ──────────────────────────────────────────────────────────
    def create_account(self, payload: dict) -> dict:
        """
        Cria subconta (parceiro) no Asaas.

        Retorna dict com `id`, `walletId`, `apiKey`.
        O `apiKey` é devolvido somente nesta resposta — persista-o.
        """
        return self._request("POST", "/accounts", json=payload)

    # ── Clientes ───────────────────────────────────────────────────────────
    def create_customer(self, payload: dict) -> dict:
        """Cria um cliente (pagador). Retorna dict com `id`."""
        return self._request("POST", "/customers", json=payload)

    # ── Cobranças ──────────────────────────────────────────────────────────
    def create_payment(self, payload: dict) -> dict:
        """Cria cobrança. Inclua `split` no payload para repasse automático."""
        return self._request("POST", "/payments", json=payload)

    def get_payment(self, payment_id: str) -> dict:
        """Consulta estado atual de uma cobrança."""
        return self._request("GET", f"/payments/{payment_id}")

    def get_pix_qrcode(self, payment_id: str) -> dict:
        """Retorna QR Code Pix de uma cobrança (encodedImage, payload)."""
        return self._request("GET", f"/payments/{payment_id}/pixQrCode")

    def list_payments(
        self,
        billing_type: str | None = None,
        status: str | None = None,
        date_created_ge: str | None = None,
        date_created_le: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """
        Lista cobranças com filtros opcionais.

        Args:
            billing_type:    'PIX' | 'BOLETO' | 'CREDIT_CARD' (None = todos)
            status:          'PENDING' | 'RECEIVED' | 'CONFIRMED' | 'OVERDUE' | etc.
            date_created_ge: 'YYYY-MM-DD' — cobranças a partir desta data
            date_created_le: 'YYYY-MM-DD' — cobranças até esta data
            limit:           máximo de registros (padrão 50)
            offset:          paginação

        Retorna: {"data": [...], "totalCount": int, "hasMore": bool, ...}
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if billing_type:
            params["billingType"] = billing_type
        if status:
            params["status"] = status
        if date_created_ge:
            params["dateCreated[ge]"] = date_created_ge
        if date_created_le:
            params["dateCreated[le]"] = date_created_le
        return self._request("GET", "/payments", params=params)


# ─── Serviço de negócio ───────────────────────────────────────────────────────

class AsaasService:
    """
    Orquestrador das regras de negócio Asaas.

    Responsabilidades:
    - Provisionar subconta de um parceiro (onboarding)
    - Calcular split (Tálya × parceiro) com base no piso e na taxa de plataforma
    - Criar cobranças com split automático
    """

    DEFAULT_PLATFORM_FEE = Decimal("10")

    def __init__(
        self,
        client: AsaasClient | None = None,
        platform_fee_percent: Decimal | None = None,
    ):
        self.client = client or AsaasClient()

        # Resolução da taxa de plataforma:
        # 1. argumento explícito
        # 2. settings.talya_platform_fee_percent / TALYA_PLATFORM_FEE_PERCENT env
        # 3. DEFAULT_PLATFORM_FEE (10%)
        if platform_fee_percent is not None:
            self.platform_fee = platform_fee_percent
        else:
            raw = _resolve_secret("TALYA_PLATFORM_FEE_PERCENT", "")
            if raw:
                self.platform_fee = Decimal(raw)
            else:
                try:
                    from app.core.config import settings
                    self.platform_fee = Decimal(str(settings.talya_platform_fee_percent))
                except Exception:
                    self.platform_fee = self.DEFAULT_PLATFORM_FEE

    # ── Onboarding ────────────────────────────────────────────────────────
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
        Cria subconta do parceiro no Asaas.

        Retorna o payload do Asaas contendo `id`, `walletId` e `apiKey`.
        O `apiKey` é devolvido somente nesta resposta — persista-o imediatamente.
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
        return self.client.create_account({k: v for k, v in payload.items() if v is not None})

    # ── Cálculo de split ──────────────────────────────────────────────────
    @staticmethod
    def compute_split(
        total: Decimal,
        floor_total: Decimal,
        platform_fee: Decimal | None = None,
    ) -> dict:
        """
        Calcula a divisão do pagamento entre parceiro e Tálya.

        Modelo:
          margem = total - floor_total
          taxa   = margem * platform_fee / 100
          parceiro recebe: margem - taxa
          tálya retém:    floor_total + taxa

        Args:
            total:        valor total pago pelo cliente
            floor_total:  soma dos preços de piso dos itens
            platform_fee: % de taxa da plataforma (padrão: settings.talya_platform_fee_percent)

        Retorna:
          {partner_amount, hipnus_amount, platform_fee}
        """
        if platform_fee is None:
            platform_fee = Decimal("0")
        margin         = max(Decimal("0"), total - floor_total)
        fee            = (margin * platform_fee / Decimal("100")).quantize(Decimal("0.01"))
        partner_amount = (margin - fee).quantize(Decimal("0.01"))
        hipnus_amount  = (total - partner_amount).quantize(Decimal("0.01"))
        return {
            "partner_amount": partner_amount,
            "hipnus_amount":  hipnus_amount,
            "platform_fee":   fee,
        }

    # ── Cobrança com split ────────────────────────────────────────────────
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
        Cria cobrança com split automático para o parceiro.

        Args:
            asaas_customer_id: ID do cliente no Asaas
            billing_type:      'PIX' | 'BOLETO' | 'CREDIT_CARD'
            value:             valor total da cobrança
            partner_wallet_id: walletId da subconta do parceiro
            partner_amount:    fixedValue repassado ao parceiro
            due_date:          'YYYY-MM-DD'
            external_reference: referência interna (ex: 'TALYA-20260101-123')
            description:       descrição visível ao cliente
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
