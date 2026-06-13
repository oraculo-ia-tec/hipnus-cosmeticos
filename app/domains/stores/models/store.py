"""
Models de lojas — vitrine individual de cada parceiro.

Entidades:
- Store: loja online do parceiro (slug único, branding básico).
- StoreListing: vínculo Loja<->Produto com o PREÇO DE VENDA escolhido pelo
  parceiro. O preço deve respeitar o piso do produto (validado em serviço).

Regra de negócio:
    StoreListing.sale_price >= Product.floor_price  (validado em service layer)
    margem do parceiro = sale_price - floor_price
"""
from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin


class Store(TimestampMixin, Base):
    __tablename__ = "stores"

    partner_id: Mapped[int] = mapped_column(
        ForeignKey("partners.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    primary_color: Mapped[str | None] = mapped_column(String(9), nullable=True)  # hex
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    partner = relationship("Partner", back_populates="store")
    listings = relationship(
        "StoreListing", back_populates="store", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Store {self.slug!r} partner={self.partner_id}>"


class StoreListing(TimestampMixin, Base):
    __tablename__ = "store_listings"
    __table_args__ = (
        UniqueConstraint("store_id", "product_id", name="uq_store_product"),
    )

    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Preço de venda definido pelo parceiro (>= floor_price do produto).
    sale_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    # Estoque controlado pelo parceiro (inclui registro de vendas físicas).
    stock_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    store = relationship("Store", back_populates="listings")
    product = relationship("Product", back_populates="store_listings")

    def __repr__(self) -> str:
        return f"<StoreListing store={self.store_id} product={self.product_id} price={self.sale_price}>"
