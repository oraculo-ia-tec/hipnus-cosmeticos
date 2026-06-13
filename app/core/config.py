"""
Configuração central da aplicação HIPNUS COSMÉTICOS.

Carrega variáveis de ambiente via Pydantic Settings. Centraliza todos os
parâmetros de infraestrutura, integrações externas (Asaas, SMTP Hostinger,
Groq) e regras de negócio globais.

Uso:
    from app.core.config import settings
    settings.ASAAS_API_KEY
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ------------------------------------------------------------------ App
    APP_NAME: str = "HIPNUS COSMÉTICOS"
    APP_ENV: Literal["local", "staging", "production"] = "local"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = Field(default="change-me-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # ------------------------------------------------------------- Database
    # Local: SQLite | Produção: MySQL (Hostinger)
    DATABASE_URL: str = "sqlite:///./data/hipnus.db"

    # ----------------------------------------------------------- Asaas API
    # Integração oficial Asaas para criação de parceiros (subcontas/wallets),
    # split de pagamento, cobranças e webhooks.
    ASAAS_API_KEY: str = Field(default="")
    ASAAS_BASE_URL: str = "https://api-sandbox.asaas.com/v3"  # produção: https://api.asaas.com/v3
    ASAAS_WEBHOOK_TOKEN: str = Field(default="")
    # Percentual de comissão da Hipnus sobre o que excede o piso (configurável).
    HIPNUS_PLATFORM_FEE_PERCENT: float = 0.0

    # --------------------------------------------------------- SMTP Hostinger
    SMTP_HOST: str = "smtp.hostinger.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    SMTP_FROM: str = "no-reply@hipnuscosmeticos.com.br"

    # --------------------------------------------------------------- Groq AI
    GROQ_API_KEY: str = Field(default="")
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # -------------------------------------------------------------- Frontend
    FRONTEND_BASE_URL: str = "http://localhost:8501"
    BACKEND_BASE_URL: str = "http://localhost:8000"


@lru_cache
def get_settings() -> Settings:
    """Retorna instância singleton de Settings (cacheada)."""
    return Settings()


settings = get_settings()
