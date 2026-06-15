"""
registry.py — Registro de modelos SQLAlchemy
=============================================
Importa todos os modelos para que o Base.metadata os conheça
before do create_all(). Adicione novos domínios aqui.
"""


def import_all_models() -> None:
    from app.domains.users.models import User          # noqa: F401
    from app.domains.catalog.models import Product     # noqa: F401
    try:
        from app.domains.orders.models import Order    # noqa: F401
    except ImportError:
        pass
    try:
        from app.domains.stores.models import Store    # noqa: F401
    except ImportError:
        pass
