"""
Serviço de parceiros — onboarding e provisionamento Asaas.

Fluxo de onboarding (create_partner):
    1. Valida unicidade (email, cpf_cnpj).
    2. Cria o registro Partner com status PENDING.
    3. Provisiona a subconta no Asaas (POST /accounts) -> wallet + apiKey.
    4. Persiste asaas_account_id / wallet / apiKey e marca status ACTIVE.
    5. Cria a Store 1:1 do parceiro.

    Caso o provisionamento Asaas falhe, o parceiro permanece PENDING para
    retentativa, sem deixar dados inconsistentes (a loja só é criada após
    sucesso no Asaas).
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.domains.partners.models.partner import Partner, PartnerStatus
from app.domains.partners.schemas.partner import PartnerCreate
from app.domains.stores.models.store import Store
from app.integrations.asaas.service import AsaasService


class PartnerService:
    def __init__(self, db: Session, asaas: AsaasService | None = None):
        self.db = db
        self.asaas = asaas or AsaasService()

    def get(self, partner_id: int) -> Partner:
        partner = self.db.get(Partner, partner_id)
        if not partner:
            raise NotFoundError(f"Parceiro {partner_id} não encontrado")
        return partner

    def _check_unique(self, email: str, cpf_cnpj: str) -> None:
        dup = self.db.scalar(
            select(Partner).where(
                (Partner.email == email) | (Partner.cpf_cnpj == cpf_cnpj)
            )
        )
        if dup:
            raise ConflictError("Já existe parceiro com este e-mail ou CPF/CNPJ")

    def create_partner(self, data: PartnerCreate, *, provision: bool = True) -> Partner:
        self._check_unique(data.email, data.cpf_cnpj)

        partner = Partner(
            name=data.name,
            legal_name=data.legal_name,
            email=data.email,
            phone=data.phone,
            cpf_cnpj=data.cpf_cnpj,
            partner_type=data.partner_type,
            status=PartnerStatus.PENDING,
        )
        self.db.add(partner)
        self.db.flush()  # garante partner.id sem commit definitivo

        if provision:
            account = self.asaas.provision_partner_account(
                name=data.name,
                email=data.email,
                cpf_cnpj=data.cpf_cnpj,
                phone=data.phone,
                income_value=data.income_value,
                postal_code=data.postal_code,
                address=data.address,
                address_number=data.address_number,
                province=data.province,
            )
            partner.asaas_account_id = account.get("id")
            partner.asaas_wallet_id = account.get("walletId")
            partner.asaas_api_key = account.get("apiKey")
            partner.status = PartnerStatus.ACTIVE

        # Cria a loja 1:1
        store = Store(
            partner_id=partner.id,
            slug=data.store_slug,
            display_name=data.store_display_name,
        )
        self.db.add(store)
        self.db.commit()
        self.db.refresh(partner)
        return partner
