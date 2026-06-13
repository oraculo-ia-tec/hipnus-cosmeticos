"""
Router de catálogo — endpoints públicos de produtos Hipnus.

Base: /api/v1/catalog
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.domains.catalog.models.product import ProductCategory
from app.domains.catalog.schemas.product import ProductCreate, ProductOut, ProductUpdate
from app.domains.catalog.services.product_service import ProductService

router = APIRouter(prefix="/catalog", tags=["Catálogo"])


@router.get("/products", response_model=list[ProductOut])
def list_products(
    category: ProductCategory | None = Query(default=None),
    line: str | None = Query(default=None, description="Linha/coleção (ex.: Turmalina)"),
    search: str | None = Query(default=None, description="Busca por nome"),
    db: Session = Depends(get_db),
):
    """
    Lista produtos ativos do catálogo oficial Hipnus.

    Parâmetros: filtros opcionais por categoria, linha e termo de busca.
    Retorno: lista de produtos com piso e preço sugerido.
    Regras de negócio: retorna apenas produtos ativos.
    """
    return ProductService(db).list(category=category, line=line, search=search)


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Retorna um produto pelo id. 404 se não existir."""
    return ProductService(db).get(product_id)


@router.post("/products", response_model=ProductOut, status_code=201)
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    """
    Cria um produto no catálogo (uso administrativo Hipnus).

    Regras: SKU único; floor_price obrigatório (>= 0).
    Efeitos colaterais: persiste novo produto disponível a todas as lojas.
    """
    return ProductService(db).create(data)


@router.patch("/products/{product_id}", response_model=ProductOut)
def update_product(product_id: int, data: ProductUpdate, db: Session = Depends(get_db)):
    """Atualiza campos de um produto (administrativo). 404 se não existir."""
    return ProductService(db).update(product_id, data)
