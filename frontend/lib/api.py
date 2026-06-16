"""
Camada de dados do frontend — consome a API FastAPI do backend.

Estratégia de resiliência:
    A vitrine deve funcionar mesmo sem o backend no ar (ex.: demonstração).
    Por isso, cada função tenta a API HTTP e, em caso de falha de conexão,
    faz *fallback* para o catálogo do seed (data/catalog_seed.json).

Cache:
    Resultados de catálogo são cacheados via st.cache_data para fluidez.
"""
from __future__ import annotations

import json
from functools import lru_cache

import httpx
import streamlit as st

from lib.config import API_V1, SEED_PATH


# --------------------------------------------------------------------- seed
@lru_cache(maxsize=1)
def _load_seed() -> dict:
    """Carrega o catálogo do arquivo de seed (fallback offline)."""
    with open(SEED_PATH, encoding="utf-8") as f:
        return json.load(f)


def _seed_products() -> list[dict]:
    products = _load_seed()["products"]
    return [
        {**p, "id": i + 1, "_source": "seed"}
        for i, p in enumerate(products)
        if p.get("active", True)
    ]


# ---------------------------------------------------------------- API status
@st.cache_data(ttl=30, show_spinner=False)
def api_online() -> bool:
    """Verifica se o backend está acessível (healthcheck)."""
    try:
        r = httpx.get(API_V1.replace("/api/v1", "/health"), timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


# ------------------------------------------------------------------ catálogo
@st.cache_data(ttl=60, show_spinner=False)
def get_products() -> list[dict]:
    """
    Retorna todos os produtos ativos do catálogo.
    Tenta a API; em falha, usa o seed. O resultado é cacheado por 60s.
    """
    try:
        r = httpx.get(f"{API_V1}/catalog/products", timeout=4.0)
        r.raise_for_status()
        data = r.json()
        return [{**p, "_source": "api"} for p in data]
    except Exception:
        return _seed_products()


def get_product(product_id: int) -> dict | None:
    """Retorna um produto pelo id (a partir da lista carregada)."""
    for p in get_products():
        if p.get("id") == product_id:
            return p
    return None


def list_lines() -> list[str]:
    lines = {p["line"] for p in get_products() if p.get("line")}
    return sorted(lines)


def list_categories() -> list[str]:
    cats = {p["category"] for p in get_products() if p.get("category")}
    return sorted(cats)


# --------------------------------------------------------------------- lojas
@st.cache_data(ttl=60, show_spinner=False)
def get_store(slug: str) -> dict | None:
    """Retorna a loja pública por slug (apenas via API)."""
    try:
        r = httpx.get(f"{API_V1}/stores/{slug}", timeout=4.0)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


@st.cache_data(ttl=60, show_spinner=False)
def get_store_listings(store_id: int) -> list[dict]:
    """Retorna as ofertas (produto + preço de venda) de uma loja, via API."""
    try:
        r = httpx.get(f"{API_V1}/stores/{store_id}/listings", timeout=4.0)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


# ------------------------------------------------------------------ convites
def send_invite(
    email: str,
    nome: str | None = None,
    mensagem: str | None = None,
    token: str | None = None,
) -> dict:
    """
    Envia um convite de parceiro via API.
    Retorna o dict do convite criado: {id, email, token, link, created_at}.
    Lança Exception se a API não estiver disponível.
    """
    payload = {"email": email}
    if nome:
        payload["nome"] = nome
    if mensagem:
        payload["mensagem"] = mensagem
    if token:
        payload["token"] = token

    r = httpx.post(f"{API_V1}/invites", json=payload, timeout=6.0)
    r.raise_for_status()
    return r.json()


def list_invites() -> list[dict]:
    """
    Lista todos os convites enviados (apenas via API).
    Retorna lista vazia em caso de falha.
    """
    try:
        r = httpx.get(f"{API_V1}/invites", timeout=4.0)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []
