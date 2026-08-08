"""
Router de pedidos — criação e consulta de pedidos nas lojas dos parceiros.

Base: /api/v1/orders
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.domains.orders.schemas import OrderCreate, OrderOut
from app.domains.orders.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Pedidos"])


@router.post("", response_model=OrderOut, status_code=201)
def create_order(data: OrderCreate, db: Session = Depends(get_db)):
    """
    Cria um pedido em uma loja de parceiro.

    Parâmetros: store_id, dados do cliente, canal (online/physical) e lista de itens.
    Retorno: pedido criado com snapshot de preços e totais calculados.
    Regras: os preços são copiados do catálogo no momento da criação.
    Efeitos colaterais: persiste Order + OrderItems no banco.
    """
    return OrderService(db).create_order(data)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """Retorna um pedido pelo id. 404 se não existir."""
    return OrderService(db).get(order_id)


@router.get("/store/{store_id}", response_model=list[OrderOut])
def list_orders_by_store(store_id: int, db: Session = Depends(get_db)):
    """Lista todos os pedidos de uma loja, do mais recente para o mais antigo."""
    return OrderService(db).list_by_store(store_id)


@router.post("/{order_id}/cancel", response_model=OrderOut)
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    """Cancela um pedido pendente. 422 se o pedido já estiver pago."""
    return OrderService(db).cancel_order(order_id)
