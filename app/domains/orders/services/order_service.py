"""
order_service.py — Domínio Orders
===================================
Serviço de pedidos: criação, confirmação de pagamento e consultas.

Regras de negócio:
  - Snapshot de preços: unit_floor_price e unit_sale_price são copiados
    do produto no momento da criação — o histórico não muda se o catálogo mudar.
  - total_amount = sum(qty * unit_sale_price)
  - floor_total  = sum(qty * unit_floor_price)
  - partner_margin_total = total_amount - floor_total
  - Ao confirmar pagamento (confirm_payment), registra a Comissão com o split.
"""
from __future__ import annotations

import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domains.catalog.models.product import Product
from app.domains.orders.models.order import (
    Commission,
    Order,
    OrderItem,
    OrderStatus,
)
from app.domains.orders.schemas import OrderCreate
from app.skills.asaas_skill import AsaasService

logger = logging.getLogger(__name__)


class OrderService:
    def __init__(self, db: Session):
        self.db = db

    # ── Consultas ──────────────────────────────────────────────────────────

    def get(self, order_id: int) -> Order:
        order = self.db.get(Order, order_id)
        if not order:
            raise NotFoundError(f"Pedido {order_id} não encontrado")
        return order

    def list_by_store(self, store_id: int) -> list[Order]:
        stmt = (
            select(Order)
            .where(Order.store_id == store_id)
            .order_by(Order.created_at.desc())
        )
        return list(self.db.scalars(stmt))

    # ── Criação ────────────────────────────────────────────────────────────

    def create_order(self, data: OrderCreate) -> Order:
        """
        Cria um pedido com snapshot de preços de cada item.

        Args:
            data: OrderCreate com store_id, dados do cliente e itens.

        Retorna: Order persistido com itens e totais calculados.

        Efeitos colaterais:
          - Persiste Order + OrderItems no banco.
        """
        total_amount = Decimal("0")
        floor_total  = Decimal("0")

        order = Order(
            store_id=data.store_id,
            customer_name=data.customer_name,
            customer_email=data.customer_email,
            customer_cpf_cnpj=data.customer_cpf_cnpj,
            channel=data.channel,
            status=OrderStatus.PENDING,
        )
        self.db.add(order)
        self.db.flush()  # garante order.id

        for item_data in data.items:
            product = self.db.get(Product, item_data.product_id)
            if not product:
                raise NotFoundError(f"Produto {item_data.product_id} não encontrado")

            floor  = Decimal(str(product.floor_price))
            sale   = item_data.unit_sale_price
            qty    = item_data.quantity

            item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                quantity=qty,
                unit_floor_price=floor,
                unit_sale_price=sale,
            )
            self.db.add(item)

            total_amount += sale  * qty
            floor_total  += floor * qty

        order.total_amount         = total_amount
        order.floor_total          = floor_total
        order.partner_margin_total = total_amount - floor_total

        self.db.commit()
        self.db.refresh(order)
        logger.info("[OrderService] Pedido #%d criado (total=%s)", order.id, order.total_amount)
        return order

    # ── Confirmação de pagamento ────────────────────────────────────────────

    def confirm_payment(self, order_id: int) -> Order:
        """
        Marca o pedido como pago e calcula a comissão (split).

        Chamado pelo webhook Asaas quando o pagamento é confirmado.

        Efeitos colaterais:
          - Atualiza Order.status para PAID.
          - Cria Commission com a divisão Hipnus × parceiro.
        """
        order = self.get(order_id)

        if order.status == OrderStatus.PAID:
            return order  # idempotente

        from decimal import Decimal as _D
        from app.core.config import settings as _s
        fee_pct = _D(str(_s.hipnus_platform_fee_percent))
        split = AsaasService.compute_split(
            _D(str(order.total_amount)),
            _D(str(order.floor_total)),
            platform_fee=fee_pct,
        )

        if not order.commission:
            commission = Commission(
                order_id=order.id,
                hipnus_amount=split["hipnus_amount"],
                partner_amount=split["partner_amount"],
                platform_fee=split["platform_fee"],
            )
            self.db.add(commission)

        order.status = OrderStatus.PAID
        self.db.commit()
        self.db.refresh(order)
        logger.info("[OrderService] Pedido #%d confirmado como PAGO", order.id)
        return order

    def cancel_order(self, order_id: int) -> Order:
        """Cancela um pedido PENDING. Pedidos PAID não podem ser cancelados aqui."""
        order = self.get(order_id)
        if order.status == OrderStatus.PAID:
            raise ValueError("Pedidos pagos não podem ser cancelados por este fluxo. Use refund.")
        order.status = OrderStatus.CANCELED
        self.db.commit()
        self.db.refresh(order)
        return order
