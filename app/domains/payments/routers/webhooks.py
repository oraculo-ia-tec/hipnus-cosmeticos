"""
Router de webhooks Asaas — recebe eventos de pagamento e atualiza pedidos.

Base: /api/v1/payments

Segurança: o Asaas envia o header `asaas-access-token` configurado no painel.
Validamos contra settings.ASAAS_WEBHOOK_TOKEN antes de processar.

Eventos tratados (MVP):
- PAYMENT_CONFIRMED / PAYMENT_RECEIVED -> marca Order como PAID e registra Commission.
- PAYMENT_REFUNDED                     -> marca Order como REFUNDED.
"""
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import get_db

router = APIRouter(prefix="/payments", tags=["Pagamentos / Webhooks"])


@router.post("/webhook", status_code=200)
async def asaas_webhook(
    request: Request,
    asaas_access_token: str | None = Header(default=None, alias="asaas-access-token"),
    db: Session = Depends(get_db),
):
    """
    Endpoint de webhook do Asaas.

    Parâmetros: corpo JSON do evento Asaas; header de autenticação.
    Retorno: 200 ao processar; 401 se o token for inválido.
    Regras de negócio: atualiza o status do pagamento/pedido conforme o evento
    e registra a comissão (split) quando confirmado.
    Efeitos colaterais: atualização de Order/Payment/Commission no banco.
    Integrações: API oficial do Asaas (notificações de cobrança).
    """
    if settings.ASAAS_WEBHOOK_TOKEN and asaas_access_token != settings.ASAAS_WEBHOOK_TOKEN:
        raise HTTPException(status_code=401, detail="Token de webhook inválido")

    payload = await request.json()
    event = payload.get("event")
    # TODO(orders): localizar Payment por asaas_payment_id e aplicar transição.
    # Implementado no módulo de pedidos (próximo ciclo) para manter o split
    # auditável em Commission. Aqui apenas reconhecemos o recebimento.
    return {"received": True, "event": event}
