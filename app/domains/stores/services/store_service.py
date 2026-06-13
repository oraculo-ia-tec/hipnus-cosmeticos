"""
Serviço de lojas — gestão de ofertas (listings) das lojas dos parceiros.

Regra de negócio central:
    O preço de venda (sale_price) definido pelo parceiro NUNCA pode ser menor
    que o piso (floor_price) do produto Hipnus. Validado aqui antes de
    qualquer persistência.
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, PriceBelowFloorError
from app.domains.catalog.models.product import Product
from app.domains.stores.models.store import Store, StoreListing
from app.domains.stores.schemas.store import StoreListingCreate, StoreListingUpdate


class StoreService:
    def __init__(self, db: Session):
        self.db = db

    def get_store(self, store_id: int) -> Store:
        store = self.db.get(Store, store_id)
        if not store:
            raise NotFoundError(f"Loja {store_id} não encontrada")
        return store

    def get_store_by_slug(self, slug: str) -> Store:
        store = self.db.scalar(select(Store).where(Store.slug == slug))
        if not store:
            raise NotFoundError(f"Loja '{slug}' não encontrada")
        return store

    def _validate_floor(self, product: Product, sale_price: Decimal) -> None:
        if Decimal(str(sale_price)) < Decimal(str(product.floor_price)):
            raise PriceBelowFloorError(
                f"Preço de venda {sale_price} abaixo do piso "
                f"{product.floor_price} do produto '{product.name}'."
            )

    def add_listing(self, store_id: int, data: StoreListingCreate) -> StoreListing:
        store = self.get_store(store_id)
        product = self.db.get(Product, data.product_id)
        if not product:
            raise NotFoundError(f"Produto {data.product_id} não encontrado")

        self._validate_floor(product, data.sale_price)

        exists = self.db.scalar(
            select(StoreListing).where(
                StoreListing.store_id == store.id,
                StoreListing.product_id == product.id,
            )
        )
        if exists:
            raise ConflictError("Produto já está na loja deste parceiro")

        listing = StoreListing(
            store_id=store.id,
            product_id=product.id,
            sale_price=data.sale_price,
            stock_qty=data.stock_qty,
            featured=data.featured,
        )
        self.db.add(listing)
        self.db.commit()
        self.db.refresh(listing)
        return listing

    def update_listing(self, listing_id: int, data: StoreListingUpdate) -> StoreListing:
        listing = self.db.get(StoreListing, listing_id)
        if not listing:
            raise NotFoundError(f"Listing {listing_id} não encontrado")
        if data.sale_price is not None:
            self._validate_floor(listing.product, data.sale_price)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(listing, field, value)
        self.db.commit()
        self.db.refresh(listing)
        return listing

    def list_listings(self, store_id: int, active_only: bool = True) -> list[StoreListing]:
        stmt = select(StoreListing).where(StoreListing.store_id == store_id)
        if active_only:
            stmt = stmt.where(StoreListing.active.is_(True))
        return list(self.db.scalars(stmt))
