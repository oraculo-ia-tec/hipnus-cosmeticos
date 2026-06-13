"""
Router de parceiros — onboarding e provisionamento Asaas.

Base: /api/v1/partners
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.domains.partners.schemas.partner import PartnerCreate, PartnerOut
from app.domains.partners.services.partner_service import PartnerService

router = APIRouter(prefix="/partners", tags=["Parceiros"])


@router.post("", response_model=PartnerOut, status_code=201)
def create_partner(
    data: PartnerCreate,
    provision: bool = Query(default=True, description="Provisionar subconta Asaas"),
    db: Session = Depends(get_db),
):
    """
    Cadastra um parceiro e provisiona sua subconta (wallet) no Asaas.

    Parâmetros: dados do parceiro + dados exigidos pelo Asaas (incomeValue,
    postalCode, endereço) + slug/nome da loja a criar.
    Retorno: parceiro criado com asaas_account_id e asaas_wallet_id.
    Regras de negócio: e-mail e CPF/CNPJ únicos; ao provisionar, a subconta
    Asaas é criada e o parceiro vira ACTIVE; loja 1:1 é criada em seguida.
    Efeitos colaterais: chamada externa POST /accounts no Asaas; criação de Store.
    Integrações: API oficial do Asaas (subcontas / split).
    """
    return PartnerService(db).create_partner(data, provision=provision)


@router.get("/{partner_id}", response_model=PartnerOut)
def get_partner(partner_id: int, db: Session = Depends(get_db)):
    """Retorna um parceiro pelo id. 404 se não existir."""
    return PartnerService(db).get(partner_id)
