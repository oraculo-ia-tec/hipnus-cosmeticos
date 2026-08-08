"""
schemas/__init__.py — Domínio Orders
======================================
Schemas Pydantic para criação e leitura de pedidos.
"""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.domains.orders.models.order import OrderChannel, OrderStatus


class OrderItemCreate(BaseModel):
    product_id:      int
    quantity:        int     = Field(..., ge=1)
    unit_sale_price: Decimal = Field(..., gt=0, description="Preço de venda no momento da compra")


class OrderCreate(BaseModel):
    store_id:          int
    customer_name:     str    = Field(..., max_length=255)
    customer_email:    str | None = None
    customer_cpf_cnpj: str | None = None
    channel:           OrderChannel = OrderChannel.ONLINE
    items:             list[OrderItemCreate] = Field(..., min_length=1)


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:               int
    order_id:         int
    product_id:       int
    product_name:     str
    quantity:         int
    unit_floor_price: Decimal
    unit_sale_price:  Decimal


class CommissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:             int
    hipnus_amount:  Decimal
    partner_amount: Decimal
    platform_fee:   Decimal


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:                   int
    store_id:             int
    customer_name:        str
    customer_email:       str | None
    customer_cpf_cnpj:    str | None
    channel:              OrderChannel
    status:               OrderStatus
    total_amount:         Decimal
    floor_total:          Decimal
    partner_margin_total: Decimal
    items:                list[OrderItemOut] = []
    commission:           CommissionOut | None = None
