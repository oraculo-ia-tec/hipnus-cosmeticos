"""Schemas Pydantic do domínio de parceiros."""
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domains.partners.models.partner import PartnerStatus, PartnerType


class PartnerBase(BaseModel):
    name: str = Field(..., max_length=255)
    legal_name: str | None = None
    email: EmailStr
    phone: str | None = None
    cpf_cnpj: str = Field(..., max_length=20)
    partner_type: PartnerType = PartnerType.REVENDEDOR


class PartnerCreate(PartnerBase):
    """Onboarding de parceiro. Campos extras exigidos pelo Asaas /accounts."""

    income_value: float = Field(..., gt=0, description="Faturamento/renda mensal (Asaas)")
    postal_code: str = Field(..., max_length=9)
    address: str
    address_number: str
    province: str = Field(..., description="Bairro")
    # Dados básicos da loja a ser criada junto ao parceiro.
    store_slug: str = Field(..., max_length=120)
    store_display_name: str = Field(..., max_length=160)


class PartnerOut(PartnerBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: PartnerStatus
    asaas_account_id: str | None = None
    asaas_wallet_id: str | None = None
