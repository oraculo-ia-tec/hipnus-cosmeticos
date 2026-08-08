
"""
queries.py — TÁLYA COSMÉTICOS
================================
Queries Python usando supabase-py para cada página do Streamlit,
organizadas por perfil de usuário (admin, distribuidor/salao, cliente).

Pré-requisito:
    pip install supabase

Uso:
    from lib.supabase_client import get_supabase
    supabase = get_supabase()
"""
from __future__ import annotations

from typing import Any
from supabase import Client


# ============================================================
# lib/supabase_client.py (referência de setup)
# ============================================================
"""
import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)

# Após login, propagar o JWT do usuário para respeitar RLS:
# supabase.postgrest.auth(access_token)
"""


# ============================================================
# 0. AUTENTICAÇÃO — pages/0_Login.py
# ============================================================

def login(supabase: Client, email: str, password: str) -> dict:
    """Autentica via Supabase Auth e retorna a sessão (access_token, user)."""
    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
    return res


def register(supabase: Client, email: str, password: str, name: str) -> dict:
    """Cria usuário no Supabase Auth. O trigger/handler deve espelhar em public.users."""
    res = supabase.auth.sign_up({
        "email": email,
        "password": password,
        "options": {"data": {"name": name}},
    })
    return res


def logout(supabase: Client) -> None:
    """Encerra a sessão do usuário. Usado no botão 'Sair' da sidebar."""
    supabase.auth.sign_out()


def get_current_profile(supabase: Client) -> dict | None:
    """Busca o perfil completo em public.users do usuário logado."""
    user = supabase.auth.get_user()
    if not user or not user.user:
        return None
    res = (
        supabase.table("users")
        .select("*")
        .eq("auth_user_id", user.user.id)
        .single()
        .execute()
    )
    return res.data


# ============================================================
# 1. DASHBOARD ADMIN — pages/0_Dashboard.py (admin/super_admin)
# ============================================================

def get_admin_kpis(supabase: Client) -> dict:
    """KPIs consolidados do painel admin (view v_admin_dashboard_kpis)."""
    res = supabase.table("v_admin_dashboard_kpis").select("*").single().execute()
    return res.data


def get_admin_sales_orders(supabase: Client, status: str | None = None, limit: int = 100) -> list[dict]:
    """Lista pedidos de venda (B2C/loja) para o dashboard admin, com filtro opcional de status."""
    query = supabase.table("v_admin_sales_orders").select("*").order("created_at", desc=True).limit(limit)
    if status:
        query = query.eq("status", status)
    res = query.execute()
    return res.data


def get_admin_supply_orders(supabase: Client, status: str | None = None, limit: int = 100) -> list[dict]:
    """Lista pedidos de abastecimento B2B (parceiro -> Tálya) para o dashboard admin."""
    query = supabase.table("v_admin_supply_orders").select("*").order("created_at", desc=True).limit(limit)
    if status:
        query = query.eq("status", status)
    res = query.execute()
    return res.data


def get_admin_central_inventory(supabase: Client) -> list[dict]:
    """Estoque central Tálya, para a aba Estoque do admin."""
    res = supabase.table("v_admin_central_inventory").select("*").order("product_name").execute()
    return res.data


def get_admin_store_inventory(supabase: Client, store_id: str | None = None) -> list[dict]:
    """Estoque por loja de parceiro, com filtro opcional por loja."""
    query = supabase.table("v_admin_store_inventory").select("*").order("store_name")
    if store_id:
        query = query.eq("store_id", store_id)
    res = query.execute()
    return res.data


def get_admin_pending_shipments(supabase: Client) -> list[dict]:
    """Entregas em aberto (pending, picking, shipped, in_transit) — aba Logística/Entrega."""
    res = (
        supabase.table("shipments")
        .select("*, sales_orders(id, store_id, customer_id)")
        .in_("status", ["pending", "picking", "shipped", "in_transit"])
        .order("created_at", desc=True)
        .execute()
    )
    return res.data


def update_shipment_status(supabase: Client, shipment_id: str, status: str, tracking_code: str | None = None) -> dict:
    """Atualiza status de entrega — usado nas abas de logística do admin."""
    payload: dict[str, Any] = {"status": status}
    if tracking_code:
        payload["tracking_code"] = tracking_code
    res = supabase.table("shipments").update(payload).eq("id", shipment_id).execute()
    return res.data


def approve_supply_order(supabase: Client, supply_order_id: str) -> dict:
    """Aprova pedido de abastecimento do parceiro (draft/placed -> approved)."""
    res = (
        supabase.table("supply_orders")
        .update({"status": "approved"})
        .eq("id", supply_order_id)
        .execute()
    )
    return res.data


# ============================================================
# 2. CATÁLOGO B2B — pages/1_Catalogo.py (distribuidor/salao)
# ============================================================

def get_partner_supply_catalog(supabase: Client, search: str | None = None) -> list[dict]:
    """Catálogo Tálya com preços diferenciados (view já filtra por price_type no RLS)."""
    query = supabase.table("v_partner_supply_catalog").select("*").order("product_name")
    if search:
        query = query.ilike("product_name", f"%{search}%")
    res = query.execute()
    return res.data


def create_supply_order_draft(supabase: Client, partner_id: str) -> dict:
    """Cria um pedido de abastecimento em rascunho para o parceiro logado."""
    res = supabase.table("supply_orders").insert({"partner_id": partner_id, "status": "draft"}).execute()
    return res.data[0]


def add_supply_order_item(supabase: Client, supply_order_id: str, product_id: str, quantity: int, unit_price: float) -> dict:
    """Adiciona item ao pedido de abastecimento em rascunho (carrinho B2B)."""
    res = (
        supabase.table("supply_order_items")
        .insert({
            "supply_order_id": supply_order_id,
            "product_id": product_id,
            "quantity": quantity,
            "unit_price": unit_price,
        })
        .execute()
    )
    return res.data[0]


def submit_supply_order(supabase: Client, supply_order_id: str) -> dict:
    """Finaliza o pedido de abastecimento (draft -> placed) — dispara fluxo de aprovação admin."""
    res = supabase.table("supply_orders").update({"status": "placed"}).eq("id", supply_order_id).execute()
    return res.data


# ============================================================
# 3. GESTÃO DA LOJA — pages/2_Minha_Loja.py (distribuidor/salao)
# ============================================================

def get_my_store(supabase: Client, partner_id: str) -> dict:
    """Busca dados da loja do parceiro logado (URL personalizada, nome, logo)."""
    res = supabase.table("stores").select("*").eq("partner_id", partner_id).single().execute()
    return res.data


def update_store_profile(supabase: Client, store_id: str, display_name: str, logo_url: str | None = None) -> dict:
    """Atualiza dados de exibição da loja."""
    payload: dict[str, Any] = {"display_name": display_name}
    if logo_url:
        payload["logo_url"] = logo_url
    res = supabase.table("stores").update(payload).eq("id", store_id).execute()
    return res.data


def get_partner_store_inventory(supabase: Client, store_id: str) -> list[dict]:
    """Estoque e preços dos produtos na vitrine do parceiro."""
    res = supabase.table("v_partner_store_inventory").select("*").eq("store_id", store_id).execute()
    return res.data


def upsert_store_product(supabase: Client, store_id: str, product_id: str, sale_price: float, is_visible: bool = True) -> dict:
    """Adiciona ou atualiza produto na vitrine da loja (gestão de produtos)."""
    res = (
        supabase.table("store_products")
        .upsert({
            "store_id": store_id,
            "product_id": product_id,
            "sale_price": sale_price,
            "is_visible": is_visible,
        }, on_conflict="store_id,product_id")
        .execute()
    )
    return res.data[0]


def get_partner_store_orders(supabase: Client, store_id: str, status: str | None = None) -> list[dict]:
    """Pedidos recebidos pela loja do parceiro (gestão de vendas)."""
    query = supabase.table("v_partner_store_orders").select("*").eq("store_id", store_id).order("created_at", desc=True)
    if status:
        query = query.eq("status", status)
    res = query.execute()
    return res.data


# ============================================================
# 4. CONVITES E LINK PERSONALIZADO — pages/3_Convites.py
# ============================================================

def create_invite_link(supabase: Client, store_id: str, link_type: str, token: str, created_by: str) -> dict:
    """Gera link de cadastro ou de acesso direto à loja do parceiro."""
    res = (
        supabase.table("invite_links")
        .insert({
            "store_id": store_id,
            "type": link_type,  # 'cadastro' ou 'acesso_direto'
            "token": token,
            "created_by": created_by,
        })
        .execute()
    )
    return res.data[0]


def get_store_invite_links(supabase: Client, store_id: str) -> list[dict]:
    """Lista links já gerados pela loja, para reenvio ou controle."""
    res = supabase.table("invite_links").select("*").eq("store_id", store_id).order("created_at", desc=True).execute()
    return res.data


def resolve_invite_token(supabase: Client, token: str) -> dict | None:
    """Resolve um token de convite ao ser acessado pelo cliente (loja + tipo)."""
    res = supabase.table("invite_links").select("*, stores(*)").eq("token", token).single().execute()
    return res.data


def link_customer_to_store(supabase: Client, store_id: str, user_id: str, origin: str) -> dict:
    """Vincula o cliente à loja do parceiro (origem: invite_link, direct_link ou manual)."""
    res = (
        supabase.table("store_customers")
        .upsert({"store_id": store_id, "user_id": user_id, "origin": origin}, on_conflict="store_id,user_id")
        .execute()
    )
    return res.data[0]


# ============================================================
# 5. CATÁLOGO DA LOJA — pages/1_Catalogo.py (cliente final)
# ============================================================

def get_store_customer_catalog(supabase: Client, store_id: str, search: str | None = None) -> list[dict]:
    """Catálogo da loja personalizada com preço final e estoque disponível."""
    query = supabase.table("v_store_customer_catalog").select("*").eq("store_id", store_id).order("product_name")
    if search:
        query = query.ilike("product_name", f"%{search}%")
    res = query.execute()
    return res.data


def get_my_linked_store(supabase: Client, user_id: str) -> dict | None:
    """Retorna a loja à qual o cliente está vinculado (define o catálogo que ele acessa)."""
    res = (
        supabase.table("store_customers")
        .select("*, stores(*)")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


# ============================================================
# 6. CARRINHO — pages/Minha_Conta -> aba Carrinho
# ============================================================
# Carrinho mantido em st.session_state (não persistido no banco no MVP).
# Ao finalizar compra, os itens do session_state são gravados de uma vez:

def create_sales_order(supabase: Client, store_id: str, customer_id: str, address_id: str | None, channel: str = "online") -> dict:
    """Cria o pedido de venda (cabeçalho) ao finalizar o carrinho."""
    res = (
        supabase.table("sales_orders")
        .insert({
            "store_id": store_id,
            "customer_id": customer_id,
            "address_id": address_id,
            "channel": channel,
            "status": "pending",
        })
        .execute()
    )
    return res.data[0]


def add_sales_order_item(supabase: Client, sales_order_id: str, product_id: str, quantity: int, unit_floor_price: float, unit_sale_price: float) -> dict:
    """Adiciona item ao pedido de venda — trigger recalcula totais automaticamente."""
    res = (
        supabase.table("sales_order_items")
        .insert({
            "sales_order_id": sales_order_id,
            "product_id": product_id,
            "quantity": quantity,
            "unit_floor_price": unit_floor_price,
            "unit_sale_price": unit_sale_price,
        })
        .execute()
    )
    return res.data[0]


# ============================================================
# 7. MINHA CONTA — Meus Pedidos / Meus Pagamentos / Configurações
# ============================================================

def get_my_orders(supabase: Client, customer_id: str) -> list[dict]:
    """Aba Meus Pedidos — histórico de compras do cliente."""
    res = (
        supabase.table("v_my_orders")
        .select("*")
        .eq("customer_id", customer_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data


def get_my_payments(supabase: Client, customer_id: str) -> list[dict]:
    """Aba Meus Pagamentos — cobranças, boletos, PIX e status."""
    res = (
        supabase.table("v_my_payments")
        .select("*")
        .eq("customer_id", customer_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data


def get_my_addresses(supabase: Client, user_id: str) -> list[dict]:
    """Aba Configurações — endereços cadastrados do cliente."""
    res = supabase.table("addresses").select("*").eq("user_id", user_id).order("is_default", desc=True).execute()
    return res.data


def upsert_address(supabase: Client, user_id: str, address: dict) -> dict:
    """Cria ou atualiza endereço do cliente na aba Configurações."""
    address["user_id"] = user_id
    res = supabase.table("addresses").upsert(address).execute()
    return res.data[0]


def update_my_profile(supabase: Client, user_id: str, name: str, phone: str | None = None) -> dict:
    """Atualiza dados pessoais na aba Configurações."""
    payload: dict[str, Any] = {"name": name}
    if phone:
        payload["phone"] = phone
    res = supabase.table("users").update(payload).eq("id", user_id).execute()
    return res.data


# ============================================================
# 8. CHIARA (IA CONSULTORA) — pages/10_Chiara.py
# ============================================================

def get_product_context_for_chiara(supabase: Client, store_id: str) -> list[dict]:
    """Busca catálogo da loja do cliente para dar contexto à IA Chiara."""
    res = (
        supabase.table("v_store_customer_catalog")
        .select("product_name, description, line_name, sale_price")
        .eq("store_id", store_id)
        .execute()
    )
    return res.data


# ============================================================
# 9. FINANCEIRO — pages/Financeiro.py (distribuidor/salao)
# ============================================================

def get_partner_commissions(supabase: Client, store_id: str) -> list[dict]:
    """Comissões/splits recebidos pela loja do parceiro."""
    res = (
        supabase.table("commissions")
        .select("*, sales_orders!inner(store_id, created_at, total_amount)")
        .eq("sales_orders.store_id", store_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data
