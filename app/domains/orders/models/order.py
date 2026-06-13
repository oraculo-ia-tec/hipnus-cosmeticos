"""
Models de pedidos — vendas realizadas nas lojas dos parceiros.

Entidades:
- Order: pedido feito por um cliente em uma loja específica. Pode ser ONLINE
  (com pagamento/split via Asaas) ou PHYSICAL (registro manual de venda
  presencial, apenas para controle de estoque e comissão).
- OrderItem: itens do pedido (snapshot de preços no momento da compra).
- Commission: registro do split — quanto vai p/ Hipnus e quanto p/ o parceiro.

Snapshot de preços:
    Os valores de piso e venda são copiados para o item no momento da compra,
    preservando histórico mesmo que o catálogo mude depois (governança/auditoria).
"""
import enum

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin


class OrderChannel(str, enum.Enum):
    ONLINE = "online"      # checkout com pagamento Asaas + split
    PHYSICAL = "physical"  # venda presencial — registro manual (sem pagamento no sistema)


class OrderStatus(str, enum.Enum):
    PENDING = "pending"        # criado, aguardando pagamento
    PAID = "paid"              # pago (confirmado via webhook Asaas)
    CANCELED = "canceled"
    REFUNDED = "refunded"
    REGISTERED = "registered"  # venda física registrada (não passa por pagamento)


class Order(TimestampMixin, Base):
    __tablename__ = "orders"

    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # Dados do cliente final (B2C/B2B) — modelo simplificado no MVP.
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_cpf_cnpj: Mapped[str | None] = mapped_column(String(20), nullable=True)

    channel: Mapped[OrderChannel] = mapped_column(
        Enum(OrderChannel), default=OrderChannel.ONLINE, nullable=False, index=True
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True
    )

    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    floor_total: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    partner_margin_total: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = relationship(
        "Payment", back_populates="order", uselist=False, cascade="all, delete-orphan"
    )
    commission = relationship(
        "Commission", back_populates="order", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Order #{self.id} store={self.store_id} {self.status.value} total={self.total_amount}>"


class OrderItem(TimestampMixin, Base):
    __tablename__ = "order_items"

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)  # snapshot
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_floor_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)  # snapshot
    unit_sale_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)   # snapshot

    order = relationship("Order", back_populates="items")


class Commission(TimestampMixin, Base):
    """Resultado do split de um pedido pago (auditoria do repasse Asaas)."""

    __tablename__ = "commissions"

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    hipnus_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    partner_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    platform_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)

    order = relationship("Order", back_populates="commission")
