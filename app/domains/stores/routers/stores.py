"""
Router de lojas — vitrine pública e gestão de ofertas do parceiro.

Base: /api/v1/stores
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.domains.stores.schemas.store import (
    StoreListingCreate,
    StoreListingOut,
    StoreListingUpdate,
    StoreOut,
)
from app.domains.stores.services.store_service import StoreService

router = APIRouter(prefix="/stores", tags=["Lojas"])


@router.get("/{slug}", response_model=StoreOut)
def get_store(slug: str, db: Session = Depends(get_db)):
    """Retorna a loja pública pelo slug (vitrine). 404 se não existir."""
    return StoreService(db).get_store_by_slug(slug)


@router.get("/{store_id}/listings", response_model=list[StoreListingOut])
def list_listings(store_id: int, db: Session = Depends(get_db)):
    """Lista as ofertas ativas (produtos + preço de venda) de uma loja."""
    return StoreService(db).list_listings(store_id)


@router.post("/{store_id}/listings", response_model=StoreListingOut, status_code=201)
def add_listing(store_id: int, data: StoreListingCreate, db: Session = Depends(get_db)):
    """
    Adiciona um produto Hipnus à loja do parceiro com preço de venda.

    Parâmetros: product_id, sale_price, stock_qty, featured.
    Retorno: oferta criada.
    Regras de negócio: sale_price NUNCA pode ser menor que o piso (floor_price)
    do produto; produto não pode estar duplicado na mesma loja.
    Efeitos colaterais: cria StoreListing vinculado à loja.
    """
    return StoreService(db).add_listing(store_id, data)


@router.patch("/listings/{listing_id}", response_model=StoreListingOut)
def update_listing(listing_id: int, data: StoreListingUpdate, db: Session = Depends(get_db)):
    """Atualiza preço/estoque/destaque de uma oferta (valida piso). 404 se inexistente."""
    return StoreService(db).update_listing(listing_id, data)
