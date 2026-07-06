"""
supabase_client.py — HIPNUS COSMÉTICOS
========================================
Cliente Supabase singleton para o frontend Streamlit.

Lê SUPABASE_URL e SUPABASE_ANON_KEY de st.secrets (Streamlit Cloud)
com fallback para variáveis de ambiente locais.

Uso:
    from lib.supabase_client import get_supabase

    supabase = get_supabase()
    data = supabase.table("users").select("*").execute()

Para propagar o JWT do usuário logado (respeita RLS):
    supabase.postgrest.auth(st.session_state["access_token"])
"""
from __future__ import annotations

import os

import streamlit as st
from supabase import Client, create_client


def _get_secret(key: str) -> str:
    """Lê de st.secrets com fallback para os.environ."""
    try:
        val = st.secrets.get(key)
        if val:
            return str(val)
    except Exception:
        pass
    return os.getenv(key, "")


@st.cache_resource
def get_supabase() -> Client:
    """
    Retorna o cliente Supabase (cached por sessão do Streamlit).

    Requer nos Secrets do Streamlit Cloud:
        SUPABASE_URL      = "https://omqcuaffmlwwusgmmzml.supabase.co"
        SUPABASE_ANON_KEY = "<sua anon key pública>"
    """
    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_ANON_KEY")

    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL e SUPABASE_ANON_KEY não encontrados. "
            "Configure nos Secrets do Streamlit Cloud ou em variáveis de ambiente."
        )

    return create_client(url, key)


def get_supabase_with_auth(access_token: str) -> Client:
    """
    Retorna cliente Supabase com JWT do usuário propagado.
    Use após login para que as políticas RLS sejam aplicadas corretamente.

    Exemplo:
        supabase = get_supabase_with_auth(st.session_state["access_token"])
    """
    client = get_supabase()
    client.postgrest.auth(access_token)
    return client
