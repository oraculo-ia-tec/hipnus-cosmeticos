"""
Configuração do frontend Streamlit da vitrine HIPNUS COSMÉTICOS.

Lê variáveis de ambiente (com defaults para desenvolvimento local) e expõe
a paleta/identidade visual da marca em um único lugar.
"""
import os
from pathlib import Path

# URL base da API FastAPI (backend). Se a API estiver offline, a camada de
# dados faz fallback para o catálogo do seed JSON (modo demonstração).
API_BASE_URL = os.getenv("HIPNUS_API_URL", "http://localhost:8000")
API_V1 = f"{API_BASE_URL}/api/v1"

# Caminho do seed (fallback offline) — relativo à raiz do projeto.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SEED_PATH = PROJECT_ROOT / "data" / "catalog_seed.json"

BRAND = {
    "name": "HIPNUS COSMÉTICOS",
    "tagline": "Tratamento capilar profissional, direto da fonte.",
    "promise": "Vitrine, compra e relacionamento direto com a Hipnus — para o "
    "consumidor final e para o profissional.",
}

# Paleta da marca (clean, premium, institucional).
COLORS = {
    "primary": "#7C3AED",       # roxo Hipnus
    "primary_dark": "#5B21B6",
    "accent": "#C4A35A",        # dourado (linha Ouro / premium)
    "ink": "#1A1430",           # texto principal
    "muted": "#6B6580",         # texto secundário
    "bg": "#FFFFFF",
    "surface": "#F6F4FB",       # fundo de cards / seções
    "border": "#E7E3F2",
    "success": "#16A34A",
}

CURRENCY = "R$"
