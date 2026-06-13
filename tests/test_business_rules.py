"""
Testes das regras de negócio centrais:
- preço de venda não pode ficar abaixo do piso (PriceBelowFloorError)
- cálculo do split (Hipnus x parceiro)
"""
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.exceptions import PriceBelowFloorError
from app.db import registry  # noqa: F401
from app.db.base import Base
from app.domains.catalog.models.product import Product
from app.domains.partners.models.partner import Partner, PartnerStatus
from app.domains.stores.models.store import Store
from app.domains.stores.schemas.store import StoreListingCreate
from app.domains.stores.services.store_service import StoreService
from app.integrations.asaas.service import AsaasService


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


def _seed_store(db) -> tuple[Store, Product]:
    product = Product(sku="HIP-TEST", name="MÁSCARA TESTE", floor_price=Decimal("39.90"))
    partner = Partner(name="Salão X", email="x@e.com", cpf_cnpj="123", status=PartnerStatus.ACTIVE)
    db.add_all([product, partner])
    db.flush()
    store = Store(partner_id=partner.id, slug="salao-x", display_name="Salão X")
    db.add(store)
    db.commit()
    return store, product


def test_listing_below_floor_is_rejected(db):
    store, product = _seed_store(db)
    svc = StoreService(db)
    with pytest.raises(PriceBelowFloorError):
        svc.add_listing(store.id, StoreListingCreate(product_id=product.id, sale_price=Decimal("29.90")))


def test_listing_at_or_above_floor_is_accepted(db):
    store, product = _seed_store(db)
    svc = StoreService(db)
    listing = svc.add_listing(
        store.id, StoreListingCreate(product_id=product.id, sale_price=Decimal("69.90"), stock_qty=10)
    )
    assert listing.sale_price == Decimal("69.90")


def test_split_no_platform_fee():
    # total 69.90, piso 39.90 -> parceiro fica com a margem (30.00), Hipnus com 39.90
    result = AsaasService.compute_split(Decimal("69.90"), Decimal("39.90"))
    assert result["partner_amount"] == Decimal("30.00")
    assert result["hipnus_amount"] == Decimal("39.90")
    assert result["platform_fee"] == Decimal("0.00")
