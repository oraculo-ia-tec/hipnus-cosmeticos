"""Schemas Pydantic do domínio de catálogo."""
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.domains.catalog.models.product import ProductCategory


class ProductBase(BaseModel):
    sku: str = Field(..., max_length=64)
    name: str = Field(..., max_length=255)
    description: str | None = None
    category: ProductCategory = ProductCategory.GERAL
    line: str | None = None
    is_kit: bool = False
    floor_price: Decimal = Field(..., ge=0, description="Piso (tabela distribuidor)")
    suggested_retail_price: Decimal | None = Field(default=None, ge=0)
    image_url: str | None = None
    active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: ProductCategory | None = None
    line: str | None = None
    floor_price: Decimal | None = Field(default=None, ge=0)
    suggested_retail_price: Decimal | None = Field(default=None, ge=0)
    image_url: str | None = None
    active: bool | None = None


class ProductOut(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
