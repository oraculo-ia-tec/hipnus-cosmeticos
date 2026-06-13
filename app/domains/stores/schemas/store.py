"""Schemas Pydantic do domínio de lojas e ofertas (listings)."""
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class StoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    partner_id: int
    slug: str
    display_name: str
    description: str | None = None
    logo_url: str | None = None
    primary_color: str | None = None
    active: bool


class StoreListingCreate(BaseModel):
    """Parceiro adiciona um produto à sua loja com preço de venda."""

    product_id: int
    sale_price: Decimal = Field(..., gt=0, description="Deve ser >= floor_price do produto")
    stock_qty: int = Field(default=0, ge=0)
    featured: bool = False


class StoreListingUpdate(BaseModel):
    sale_price: Decimal | None = Field(default=None, gt=0)
    stock_qty: int | None = Field(default=None, ge=0)
    featured: bool | None = None
    active: bool | None = None


class StoreListingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    store_id: int
    product_id: int
    sale_price: Decimal
    stock_qty: int
    featured: bool
    active: bool
