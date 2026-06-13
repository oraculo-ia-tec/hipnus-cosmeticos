"""Serviço de catálogo — operações sobre produtos Hipnus."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.domains.catalog.models.product import Product, ProductCategory
from app.domains.catalog.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    def __init__(self, db: Session):
        self.db = db

    def list(
        self,
        *,
        category: ProductCategory | None = None,
        line: str | None = None,
        active_only: bool = True,
        search: str | None = None,
    ) -> list[Product]:
        stmt = select(Product)
        if active_only:
            stmt = stmt.where(Product.active.is_(True))
        if category:
            stmt = stmt.where(Product.category == category)
        if line:
            stmt = stmt.where(Product.line == line)
        if search:
            stmt = stmt.where(Product.name.ilike(f"%{search}%"))
        return list(self.db.scalars(stmt.order_by(Product.name)))

    def get(self, product_id: int) -> Product:
        product = self.db.get(Product, product_id)
        if not product:
            raise NotFoundError(f"Produto {product_id} não encontrado")
        return product

    def get_by_sku(self, sku: str) -> Product | None:
        return self.db.scalar(select(Product).where(Product.sku == sku))

    def create(self, data: ProductCreate) -> Product:
        if self.get_by_sku(data.sku):
            raise ConflictError(f"SKU {data.sku} já existe")
        product = Product(**data.model_dump())
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def update(self, product_id: int, data: ProductUpdate) -> Product:
        product = self.get(product_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(product, field, value)
        self.db.commit()
        self.db.refresh(product)
        return product
