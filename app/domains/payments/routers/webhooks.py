"""
Router de pagamentos — webhook Asaas e consulta de status.

Base: /api/v1/payments
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import get_db
from app.domains.payments.services import PaymentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Pagamentos"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class AsaasWebhookPayload(BaseModel):
    """Payload do webhook Asaas."""

    event:   str
    payment: dict


class AsaasPaymentItem(BaseModel):
    id:    str
    value: float | None = None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/webhook", status_code=200, summary="Webhook de eventos Asaas")
def asaas_webhook(
    payload: AsaasWebhookPayload,
    asaas_access_token: str | None = Header(default=None, alias="asaas-access-token"),
    db: Session = Depends(get_db),
):
    """
    Recebe eventos de pagamento do Asaas e atualiza o status interno.

    Validação: header `asaas-access-token` deve coincidir com
    `settings.asaas_webhook_token` (definido em .env / st.secrets).

    Eventos processados:
      PAYMENT_CONFIRMED / PAYMENT_RECEIVED → pedido marcado como PAGO + comissão
      PAYMENT_OVERDUE                      → status OVERDUE
      PAYMENT_REFUNDED                     → status REFUNDED
      PAYMENT_DELETED                      → status CANCELED

    Outros eventos são aceitos com HTTP 200 (ignorados silenciosamente).

    Efeitos colaterais:
      - Atualiza Payment.status no banco.
      - Ao confirmar pagamento: cria Commission e marca Order.status=PAID.
    """
    # Valida token do webhook
    webhook_token = getattr(settings, "asaas_webhook_token", "")
    if webhook_token and asaas_access_token != webhook_token:
        raise HTTPException(status_code=401, detail="Token de webhook inválido.")

    payment_id = payload.payment.get("id")
    if not payment_id:
        raise HTTPException(status_code=400, detail="Payload inválido: 'payment.id' ausente.")

    svc = PaymentService(db)
    result = svc.process_webhook(
        event=payload.event,
        asaas_payment_id=payment_id,
    )

    if result is None:
        return {"message": f"Evento '{payload.event}' ignorado.", "event": payload.event}

    return {
        "message": "Pagamento atualizado.",
        "asaas_payment_id": payment_id,
        "status": result.status.value,
    }


@router.get("/{payment_id}/status", summary="Consulta status de um pagamento")
def get_payment_status(payment_id: str, db: Session = Depends(get_db)):
    """
    Retorna o status atual de uma cobrança pelo ID Asaas.
    404 se o pagamento não existir no banco local.
    """
    svc = PaymentService(db)
    payment = svc.get_by_asaas_id(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado.")
    return {
        "asaas_payment_id": payment.asaas_payment_id,
        "status":           payment.status.value,
        "method":           payment.method.value,
        "amount":           payment.amount,
        "order_id":         payment.order_id,
        "invoice_url":      payment.invoice_url,
    }
