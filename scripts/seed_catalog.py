"""
Seed do catálogo Hipnus no banco a partir de data/catalog_seed.json.

Idempotente: produtos são criados/atualizados pelo SKU (upsert simples).
As categorias do JSON são mapeadas para o enum ProductCategory.

Uso:
    python -m scripts.seed_catalog
"""
import json
from decimal import Decimal
from pathlib import Path

from app.db import registry  # noqa: F401  (registra models)
from app.db.base import Base, SessionLocal, engine
from app.domains.catalog.models.product import Product, ProductCategory

SEED_FILE = Path(__file__).resolve().parents[1] / "data" / "catalog_seed.json"

_CATEGORY_MAP = {c.value: c for c in ProductCategory}


def _category(raw: str) -> ProductCategory:
    return _CATEGORY_MAP.get(raw, ProductCategory.GERAL)


def run() -> None:
    Base.metadata.create_all(bind=engine)
    data = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    products = data["products"]

    db = SessionLocal()
    created = updated = 0
    try:
        for p in products:
            existing = db.query(Product).filter(Product.sku == p["sku"]).one_or_none()
            srp = p.get("suggested_retail_price")
            values = dict(
                name=p["name"],
                category=_category(p["category"]),
                line=p.get("line"),
                is_kit=p.get("is_kit", False),
                floor_price=Decimal(str(p["floor_price"])),
                suggested_retail_price=Decimal(str(srp)) if srp is not None else None,
                active=p.get("active", True),
            )
            if existing:
                for k, v in values.items():
                    setattr(existing, k, v)
                updated += 1
            else:
                db.add(Product(sku=p["sku"], **values))
                created += 1
        db.commit()
    finally:
        db.close()

    print(f"Seed concluído: {created} criados, {updated} atualizados "
          f"({len(products)} no arquivo).")


if __name__ == "__main__":
    run()
