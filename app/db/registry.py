"""
Registro central de models.

Importa todos os models para que `Base.metadata` conheça todas as tabelas
ao executar `create_all` (criação de schema) e para resolver relacionamentos
declarados por string entre domínios.
"""
from app.domains.catalog.models.product import Product  # noqa: F401
from app.domains.orders.models.order import (  # noqa: F401
    Commission,
    Order,
    OrderItem,
)
from app.domains.partners.models.partner import Partner  # noqa: F401
from app.domains.payments.models.payment import Payment  # noqa: F401
from app.domains.stores.models.store import Store, StoreListing  # noqa: F401

__all__ = [
    "Product",
    "Partner",
    "Store",
    "StoreListing",
    "Order",
    "OrderItem",
    "Commission",
    "Payment",
]
