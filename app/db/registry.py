"""
registry.py — Registro de modelos SQLAlchemy
=============================================
Importa todos os modelos para que o Base.metadata os conheça
antes do create_all(). Adicione novos domínios aqui.
"""


def import_all_models() -> None:
    from app.domains.users.models import User          # noqa: F401
    from app.domains.catalog.models import Product     # noqa: F401
    try:
        from app.domains.invites.models import Invite  # noqa: F401
    except ImportError:
        pass
    try:
        from app.domains.partners.models.parceiros import Parceiro, AppConfig  # noqa: F401
    except ImportError:
        pass
    try:
        from app.domains.partners.models.partner import Partner  # noqa: F401
    except ImportError:
        pass
    try:
        from app.domains.orders.models.order import Order, OrderItem, Commission  # noqa: F401
    except ImportError:
        pass
    try:
        from app.domains.payments.models.payment import Payment  # noqa: F401
    except ImportError:
        pass
    try:
        from app.domains.stores.models.store import Store, StoreListing  # noqa: F401
    except ImportError:
        pass
