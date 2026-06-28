"""
checkout_service.py — HIPNUS COSMÉTICOS
=========================================
Camada de serviço de checkout para uso direto no Streamlit,
100% autônomo — SEM dependência do app/ (FastAPI).

Responsabilidades:
  1. Registrar ou recuperar o cliente no Asaas pelo CPF/CNPJ.
  2. Calcular o split (Hipnus × parceiro) com base no floor_price.
  3. Criar a cobrança com split automático via AsaasClient local.
  4. Retornar os dados de pagamento (link, QR Code Pix, etc.).
  5. Registrar o pedido no st.session_state (histórico da sessão).

Depêndencias internas:
  - lib.asaas_client  (AsaasClient, AsaasService, AsaasError)  ← 100% local

Sem FastAPI, sem app/, sem httpx para backend interno.
"""
from __future__ import annotations

import os
from decimal import Decimal
from datetime import date, timedelta

from lib.asaas_client import AsaasClient, AsaasService, AsaasError  # noqa: F401


# ─── Helpers ────────────────────────────────────────────────────────────────────────────────
def _get_secret(key: str, default: str = "") -> str:
    """
    Lê segredo tentando (em ordem):
      1. st.secrets["asaas"][key]   ← seção [asaas] no secrets.toml  ✔️
      2. st.secrets[key]            ← raiz do secrets.toml
      3. os.environ[key]            ← variável de ambiente
    """
    try:
        import streamlit as st
        # 1. seção [asaas]
        try:
            val = st.secrets["asaas"][key]
            if val is not None and str(val).strip():
                return str(val).strip()
        except Exception:
            pass
        # 2. raiz do secrets.toml
        try:
            val = st.secrets[key]
            if val is not None and str(val).strip():
                return str(val).strip()
        except Exception:
            pass
    except Exception:
        pass
    # 3. variável de ambiente
    return os.environ.get(key, default)


def _due_date(days: int = 3) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


def _build_external_ref(cart) -> str:
    """Aceita dict {id: item} ou list [item]."""
    if isinstance(cart, dict):
        ids = "-".join(str(v["id"]) for v in cart.values())
    else:
        ids = "-".join(str(v["id"]) for v in cart)
    return f"HIPNUS-{date.today().strftime('%Y%m%d')}-{ids}"


# ─── Função de módulo — importada por commerce.py ────────────────────────────────────────────────
def processar_checkout(
    *,
    cart: list,
    usuario: dict,
    metodo: str = "PIX",
) -> dict:
    """
    Função de entrada chamada pelo checkout_view() em commerce.py.

    Converte:
      - cart (lista de itens de session_state["cart"].values())
      - usuario (dict do usuário autenticado: name, email, cpf_cnpj, phone)
      - metodo: 'PIX' | 'BOLETO' | 'CREDIT_CARD'

    Retorna dict com: ok, payment_id, status, invoice_url,
                      pix_qrcode, pix_payload, totais, external_ref, erro.
    """
    try:
        # Converte lista → dict para compatibilidade com CheckoutService
        if isinstance(cart, list):
            cart_dict = {item["id"]: item for item in cart}
        else:
            cart_dict = cart

        if not cart_dict:
            return {"ok": False, "erro": "Carrinho vazio."}

        # Monta o dict cliente a partir do usuário autenticado
        cliente = {
            "name":    usuario.get("name") or usuario.get("username", "Cliente"),
            "cpfCnpj": usuario.get("cpf_cnpj") or usuario.get("cpf") or "00000000000",
            "email":   usuario.get("email", ""),
            "phone":   usuario.get("phone") or usuario.get("telefone", ""),
        }

        svc = CheckoutService()
        resultado = svc.processar(
            cart=cart_dict,
            billing_type=metodo,
            cliente=cliente,
        )
        resultado["ok"] = True
        # Garante que totais é serialízável (Decimal → float)
        totais = resultado.get("totais", {})
        resultado["totais"] = {k: float(v) for k, v in totais.items()}
        return resultado

    except AsaasError as exc:
        return {"ok": False, "erro": str(exc)}
    except Exception as exc:
        return {"ok": False, "erro": str(exc)}


# ─── Classe principal ────────────────────────────────────────────────────────────────────────────────
class CheckoutService:
    """
    Orquestra o fluxo completo de checkout diretamente no Streamlit.

    Uso básico:
        svc = CheckoutService()
        resultado = svc.processar(
            cart=st.session_state["cart"],
            billing_type="PIX",
            cliente={"name": ..., "cpfCnpj": ..., "email": ..., "phone": ...},
        )
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        _api_key  = api_key  or _get_secret("ASAAS_API_KEY")
        _base_url = base_url or _get_secret(
            "ASAAS_BASE_URL", "https://api-sandbox.asaas.com/v3"
        )
        self.client  = AsaasClient(api_key=_api_key, base_url=_base_url)
        self.service = AsaasService(client=self.client)

    def calcular_totais(self, cart: dict) -> dict:
        total       = Decimal("0")
        floor_total = Decimal("0")
        for item in cart.values():
            qty         = Decimal(str(item.get("qty", 1)))
            price       = Decimal(str(item.get("price", 0)))
            floor_price = Decimal(str(item.get("floor_price", item.get("price", 0))))
            total       += price * qty
            floor_total += floor_price * qty
        split = self.service.compute_split(total, floor_total)
        return {
            "total":          total,
            "floor_total":    floor_total,
            "partner_amount": split["partner_amount"],
            "hipnus_amount":  split["hipnus_amount"],
            "platform_fee":   split["platform_fee"],
        }

    def registrar_cliente(self, nome: str, cpf_cnpj: str, email: str, fone: str = "") -> str:
        payload: dict = {"name": nome, "cpfCnpj": cpf_cnpj, "email": email}
        if fone:
            payload["mobilePhone"] = fone
        resultado = self.client.create_customer(payload)
        return resultado["id"]

    def processar(
        self,
        *,
        cart: dict,
        billing_type: str,
        cliente: dict,
        partner_wallet_id: str | None = None,
        descricao: str = "Pedido HIPNUS COSMÉTICOS",
    ) -> dict:
        wallet_id = partner_wallet_id or _get_secret("PARTNER_WALLET_ID", "")
        totais    = self.calcular_totais(cart)
        ext_ref   = _build_external_ref(cart)

        customer_id = self.registrar_cliente(
            nome=cliente["name"],
            cpf_cnpj=cliente["cpfCnpj"],
            email=cliente["email"],
            fone=cliente.get("phone", ""),
        )

        if wallet_id:
            cobranca = self.service.create_charge_with_split(
                asaas_customer_id=customer_id,
                billing_type=billing_type,
                value=totais["total"],
                partner_wallet_id=wallet_id,
                partner_amount=totais["partner_amount"],
                due_date=_due_date(),
                external_reference=ext_ref,
                description=descricao,
            )
        else:
            cobranca = self.client.create_payment({
                "customer":          customer_id,
                "billingType":       billing_type,
                "value":             float(totais["total"]),
                "dueDate":           _due_date(),
                "externalReference": ext_ref,
                "description":       descricao,
            })

        payment_id = cobranca.get("id", "")
        resultado  = {
            "payment_id":   payment_id,
            "status":       cobranca.get("status", ""),
            "invoice_url":  cobranca.get("invoiceUrl") or cobranca.get("bankSlipUrl", ""),
            "pix_qrcode":   "",
            "pix_payload":  "",
            "totais":       totais,
            "external_ref": ext_ref,
        }

        if billing_type == "PIX" and payment_id:
            try:
                pix = self.client.get_pix_qrcode(payment_id)
                resultado["pix_qrcode"]  = pix.get("encodedImage", "")
                resultado["pix_payload"] = pix.get("payload", "")
            except AsaasError:
                pass

        return resultado
