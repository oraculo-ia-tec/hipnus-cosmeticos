"""
services/__init__.py — Domínio Payments
=========================================
Serviço de pagamentos: criação de cobranças no Asaas e processamento de webhooks.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domains.orders.models.order import Order, OrderStatus
from app.domains.orders.services.order_service import OrderService
from app.domains.payments.models.payment import Payment, PaymentMethod, PaymentStatus
from app.skills.asaas_skill import AsaasClient, AsaasService

logger = logging.getLogger(__name__)

# Mapeamento de eventos Asaas → PaymentStatus interno
ASAAS_EVENT_MAP: dict[str, PaymentStatus] = {
    "PAYMENT_CONFIRMED":      PaymentStatus.CONFIRMED,
    "PAYMENT_RECEIVED":       PaymentStatus.RECEIVED,
    "PAYMENT_OVERDUE":        PaymentStatus.OVERDUE,
    "PAYMENT_REFUNDED":       PaymentStatus.REFUNDED,
    "PAYMENT_DELETED":        PaymentStatus.CANCELED,
    "PAYMENT_CHARGEBACK_DISPUTE": PaymentStatus.REFUNDED,
}


class PaymentService:
    def __init__(self, db: Session, asaas_client: AsaasClient | None = None):
        self.db     = db
        self.asaas  = AsaasService(client=asaas_client)
        self.client = self.asaas.client

    # ── Consultas ──────────────────────────────────────────────────────────

    def get_by_order(self, order_id: int) -> Payment | None:
        return self.db.scalar(
            select(Payment).where(Payment.order_id == order_id)
        )

    def get_by_asaas_id(self, asaas_payment_id: str) -> Payment | None:
        return self.db.scalar(
            select(Payment).where(Payment.asaas_payment_id == asaas_payment_id)
        )

    # ── Criação de cobrança ────────────────────────────────────────────────

    def create_charge(
        self,
        *,
        order_id: int,
        billing_type: str,
        cpf_cnpj: str,
        customer_name: str,
        customer_email: str | None,
        partner_wallet_id: str,
        due_days: int = 3,
    ) -> Payment:
        """
        Cria uma cobrança no Asaas com split automático para o parceiro.

        Fluxo:
          1. Cria ou recupera o cliente no Asaas pelo CPF/CNPJ.
          2. Calcula o split (parceiro × Tálya) via AsaasService.
          3. Cria a cobrança com split configurado.
          4. Persiste o Payment no banco.

        Args:
            order_id:          ID do pedido vinculado
            billing_type:      'PIX' | 'BOLETO' | 'CREDIT_CARD'
            cpf_cnpj:          CPF/CNPJ do pagador (para cadastro no Asaas)
            customer_name:     nome do pagador
            customer_email:    e-mail do pagador (opcional)
            partner_wallet_id: walletId da subconta do parceiro
            due_days:          vencimento em dias (padrão 3)

        Retorna: Payment persistido com asaas_payment_id e invoice_url.
        """
        order = self.db.get(Order, order_id)
        if not order:
            raise NotFoundError(f"Pedido {order_id} não encontrado")

        # Cria/recupera cliente no Asaas
        customer_payload: dict = {
            "name":    customer_name,
            "cpfCnpj": cpf_cnpj,
        }
        if customer_email:
            customer_payload["email"] = customer_email

        asaas_customer = self.client.create_customer(customer_payload)
        asaas_customer_id = asaas_customer["id"]

        # Calcula split
        total       = Decimal(str(order.total_amount))
        floor_total = Decimal(str(order.floor_total))
        from app.core.config import settings as _settings
        fee_pct = Decimal(str(_settings.talya_platform_fee_percent))
        split   = self.asaas.compute_split(total, floor_total, platform_fee=fee_pct)

        # Cria cobrança com split
        due_date = (date.today() + timedelta(days=due_days)).isoformat()
        charge   = self.asaas.create_charge_with_split(
            asaas_customer_id=asaas_customer_id,
            billing_type=billing_type,
            value=total,
            partner_wallet_id=partner_wallet_id,
            partner_amount=split["partner_amount"],
            due_date=due_date,
            external_reference=f"TALYA-{date.today().strftime('%Y%m%d')}-{order.id}",
            description=f"Pedido Tálya #{order.id}",
        )

        payment = Payment(
            order_id=order.id,
            asaas_payment_id=charge.get("id"),
            asaas_customer_id=asaas_customer_id,
            invoice_url=charge.get("invoiceUrl"),
            method=PaymentMethod(billing_type) if billing_type in PaymentMethod.__members__ else PaymentMethod.UNDEFINED,
            status=PaymentStatus.PENDING,
            amount=float(total),
        )

        # Pix QR Code (se aplicável)
        if billing_type == "PIX" and charge.get("id"):
            try:
                pix = self.client.get_pix_qrcode(charge["id"])
                payment.pix_qr_code = pix.get("payload") or pix.get("encodedImage")
            except Exception as exc:
                logger.warning("[PaymentService] QR Code Pix não disponível: %s", exc)

        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        logger.info(
            "[PaymentService] Cobrança criada: asaas_id=%s order=%d",
            payment.asaas_payment_id,
            order.id,
        )
        return payment

    # ── Processamento de webhook ────────────────────────────────────────────

    def process_webhook(self, event: str, asaas_payment_id: str) -> Payment | None:
        """
        Processa evento de webhook do Asaas.

        Mapeamento de eventos:
          PAYMENT_CONFIRMED / PAYMENT_RECEIVED → CONFIRMED (pedido marcado PAID)
          PAYMENT_OVERDUE                      → OVERDUE
          PAYMENT_REFUNDED                     → REFUNDED
          PAYMENT_DELETED                      → CANCELED

        Args:
            event:             nome do evento Asaas (ex: 'PAYMENT_CONFIRMED')
            asaas_payment_id:  ID da cobrança no Asaas

        Retorna: Payment atualizado, ou None se o evento for ignorado.
        """
        new_status = ASAAS_EVENT_MAP.get(event)
        if new_status is None:
            logger.debug("[PaymentService] Evento ignorado: %s", event)
            return None

        payment = self.get_by_asaas_id(asaas_payment_id)
        if not payment:
            logger.warning(
                "[PaymentService] Cobrança não encontrada: %s", asaas_payment_id
            )
            return None

        payment.status = new_status
        self.db.commit()

        # Se confirmado, marca o pedido como pago e gera comissão
        if new_status in (PaymentStatus.CONFIRMED, PaymentStatus.RECEIVED):
            try:
                OrderService(self.db).confirm_payment(payment.order_id)
            except Exception as exc:
                logger.error(
                    "[PaymentService] Erro ao confirmar pedido %d: %s",
                    payment.order_id,
                    exc,
                )

        self.db.refresh(payment)
        logger.info(
            "[PaymentService] Webhook processado: %s → %s",
            event,
            new_status.value,
        )
        return payment
