"""
Configuração do frontend Streamlit da vitrine HIPNUS COSMÉTICOS.

Lê variáveis de ambiente / Streamlit Secrets (st.secrets ou os.environ)
com defaults seguros para desenvolvimento local.

Nomes de variáveis alinhados com o bloco [email] do Streamlit Secrets:
    EMAIL_HOST, EMAIL_PORT, EMAIL_USERNAME, EMAIL_PASSWORD,
    EMAIL_USE_TLS, EMAIL_REMETENTE
"""
import os
from pathlib import Path

import streamlit as st


def _secret(key: str, default: str = "") -> str:
    """Lê do st.secrets (Streamlit Cloud) ou de os.environ, com fallback."""
    try:
        # Tenta primeiro no bloco [email] do secrets.toml
        return str(st.secrets["email"].get(key, os.getenv(key, default)))
    except Exception:
        return os.getenv(key, default)


# ─ API Backend ───────────────────────────────────────────
API_BASE_URL = os.getenv("HIPNUS_API_URL", "http://localhost:8000")
API_V1       = f"{API_BASE_URL}/api/v1"

# ─ Paths ───────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SEED_PATH    = PROJECT_ROOT / "data" / "catalog_seed.json"

# ─ App URL ────────────────────────────────────────────
APP_URL = os.getenv("HIPNUS_APP_URL", "https://hipnus-cosmeticos.streamlit.app")

# ─ SMTP (lido dos Secrets do Streamlit Cloud, bloco [email]) ───────
SMTP_HOST      = _secret("EMAIL_HOST",       "smtp.hostinger.com")
SMTP_PORT      = int(_secret("EMAIL_PORT",   "587"))
SMTP_USER      = _secret("EMAIL_USERNAME",   "")
SMTP_PASS      = _secret("EMAIL_PASSWORD",   "")
SMTP_USE_TLS   = _secret("EMAIL_USE_TLS",    "true").lower() == "true"
SMTP_USE_SSL   = _secret("EMAIL_USE_SSL",    "false").lower() == "true"
SMTP_REMETENTE = _secret("EMAIL_REMETENTE",  SMTP_USER)

# ─ Identidade da marca ──────────────────────────────────
BRAND = {
    "name":    "HIPNUS COSMÉTICOS",
    "tagline": "Tratamento capilar profissional, direto da fonte.",
    "promise": "Vitrine, compra e relacionamento direto com a Hipnus — para o "
               "consumidor final e para o profissional.",
}

# Paleta da marca (clean, premium, institucional).
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
