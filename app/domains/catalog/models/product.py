"""
Models de catálogo — produtos da marca Hipnus Cosméticos.

Entidades:
- Product: produto oficial do portfólio Hipnus (fonte única de verdade).
  Possui `floor_price` (piso = tabela distribuidor 2026), abaixo do qual
  nenhum parceiro pode vender, e `suggested_retail_price` (sugestão de varejo).

Regra de negócio central:
    preço de venda do parceiro >= product.floor_price
"""
import enum

from sqlalchemy import Boolean, Enum, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin


class ProductCategory(str, enum.Enum):
    """Categorias macro do catálogo (derivadas das tabelas oficiais 2026)."""

    TRATAMENTO_OBRIGATORIO = "Tratamento Obrigatorio"
    HOME_CARE = "Home Care"
    QUIMICAS = "Quimicas"
    MASCARAS_AVULSAS = "Mascaras Avulsas"
    MASCARAS_MATIZADORAS = "Mascaras Matizadoras"
    MATIZADORES = "Matizadores"
    LINHA_MASCULINA = "Linha Masculina"
    ENCAPSULADOS = "Encapsulados"
    MASCARA_LIQUIDA = "Mascara Liquida"
    DIVERSOS = "Diversos"
    GERAL = "Geral"


class Product(TimestampMixin, Base):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    category: Mapped[ProductCategory] = mapped_column(
        Enum(ProductCategory), default=ProductCategory.GERAL, nullable=False, index=True
    )
    # Linha/coleção da marca (Turmalina, Ouro, Teia de Aranha, etc.)
    line: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)

    is_kit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Preço PISO (tabela distribuidor) — custo mínimo que o parceiro paga à Hipnus
    # e abaixo do qual não pode revender.
    floor_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    # Preço sugerido ao consumidor final (referência da Hipnus).
    suggested_retail_price: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relacionamento: preços/ofertas que cada loja de parceiro define p/ este produto.
    store_listings = relationship(
        "StoreListing", back_populates="product", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Product {self.sku} {self.name!r} floor={self.floor_price}>"
