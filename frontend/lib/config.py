"""
config.py — HIPNUS COSMÉTICOS
================================
Configuração do frontend Streamlit.

Lê variáveis de ambiente / Streamlit Secrets com defaults seguros.
Não depende do app/ (FastAPI) — o frontend é 100% autônomo.

Variáveis suportadas (Secrets ou ENV):
  ASAAS_API_KEY            → chave da conta raiz Hipnus no Asaas
  ASAAS_BASE_URL           → URL da API Asaas (padrão: sandbox)
  PARTNER_WALLET_ID        → walletId do parceiro para split automático
  HIPNUS_PLATFORM_FEE_PERCENT → taxa de plataforma em % (padrão: 10)
  HIPNUS_APP_URL           → URL pública do app Streamlit
  DATABASE_URL             → URL do banco (SQLite local ou MySQL Hostinger)
  EMAIL_HOST / PORT / USERNAME / PASSWORD / USE_TLS / USE_SSL / REMETENTE

Variáveis legadas (mantidas para compatibilidade; não usadas pelo checkout):
  HIPNUS_API_URL           → URL do backend FastAPI (futuro)
"""
from __future__ import annotations

import os
from pathlib import Path

import streamlit as st


def _secret(key: str, default: str = "") -> str:
    """Lê do bloco raiz ou [email] do st.secrets, com fallback para os.environ."""
    try:
        val = st.secrets.get(key)
        if val:
            return str(val)
    except Exception:
        pass
    try:
        val = st.secrets["email"].get(key)
        if val:
            return str(val)
    except Exception:
        pass
    return os.getenv(key, default)


# ─── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SEED_PATH    = PROJECT_ROOT / "data" / "catalog_seed.json"

# ─── App URL ──────────────────────────────────────────────────────────────────
APP_URL = os.getenv("HIPNUS_APP_URL", "https://hipnus-cosmeticos.streamlit.app")

# ─── Backend FastAPI (legado — mantido para compatibilidade futura) ───────────
# Usado apenas por api.py (catálogo com fallback) e 6_Convites.py.
# O checkout NÃO depende desta URL.
API_BASE_URL = os.getenv("HIPNUS_API_URL", "http://localhost:8000")
API_V1       = f"{API_BASE_URL}/api/v1"

# ─── SMTP ─────────────────────────────────────────────────────────────────────
SMTP_HOST      = _secret("EMAIL_HOST",       "smtp.hostinger.com")
SMTP_PORT      = int(_secret("EMAIL_PORT",   "587"))
SMTP_USER      = _secret("EMAIL_USERNAME",   "")
SMTP_PASS      = _secret("EMAIL_PASSWORD",   "")
SMTP_USE_TLS   = _secret("EMAIL_USE_TLS",    "true").lower()  == "true"
SMTP_USE_SSL   = _secret("EMAIL_USE_SSL",    "false").lower() == "true"
SMTP_REMETENTE = _secret("EMAIL_REMETENTE",  SMTP_USER)

# ─── Identidade da marca ──────────────────────────────────────────────────────
BRAND = {
    "name":    "HIPNUS COSMÉTICOS",
    "tagline": "Tratamento capilar profissional, direto da fonte.",
    "promise": "Vitrine, compra e relacionamento direto com a Hipnus — "
               "para o consumidor final e para o profissional.",
}

# ─── Paleta da marca ──────────────────────────────────────────────────────────
COLORS = {
    "primary":      "#7C3AED",
    "primary_dark": "#5B21B6",
    "accent":       "#C4A35A",
    "ink":          "#1A1430",
    "muted":        "#6B6580",
    "bg":           "#FFFFFF",
    "surface":      "#F6F4FB",
    "border":       "#E7E3F2",
    "success":      "#16A34A",
}

CURRENCY = "R$"
