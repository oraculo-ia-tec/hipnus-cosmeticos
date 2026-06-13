"""
Models de pagamentos — cobranças Asaas vinculadas a pedidos online.

Entidades:
- Payment: cobrança gerada no Asaas (Pix / cartão / boleto) com split
  configurado para o parceiro. Reflete o estado do pagamento conforme
  webhooks oficiais do Asaas.
"""
import enum

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin


class PaymentMethod(str, enum.Enum):
    PIX = "PIX"
    CREDIT_CARD = "CREDIT_CARD"
    BOLETO = "BOLETO"
    UNDEFINED = "UNDEFINED"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    RECEIVED = "RECEIVED"
    OVERDUE = "OVERDUE"
    REFUNDED = "REFUNDED"
    CANCELED = "CANCELED"


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    # Identificadores Asaas
    asaas_payment_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    asaas_customer_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    invoice_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    pix_qr_code: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod), default=PaymentMethod.UNDEFINED, nullable=False
    )
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False, index=True
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="payment")
