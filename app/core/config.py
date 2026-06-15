"""
config.py — HIPNUS COSMÉTICOS
================================
Configurações globais da aplicação via Pydantic Settings.
Todas as variáveis são lidas do ambiente (.env) com valores padrão para dev.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name:    str = "HIPNUS COSMÉTICOS"
    app_version: str = "0.1.0"
    debug:       bool = True

    # JWT
    secret_key:        str = "hipnus-dev-secret-change-in-production"
    access_token_minutes: int = 480  # 8 horas

    # Banco de dados
    database_url: str = "sqlite:///./data/hipnus.db"

    # Admin padrão (criado no startup se não existir)
    admin_username: str = "william"
    admin_name:     str = "William Eustáquio"
    admin_email:    str = "programador.descpro@gmail.com"
    admin_password: str = "hipnus@2026"

    # Asaas
    asaas_api_key:  str = ""
    asaas_base_url: str = "https://api-sandbox.asaas.com/v3"
    partner_wallet_id: str = ""

    # SMTP Hostinger
    smtp_host:     str = ""
    smtp_port:     int = 587
    smtp_user:     str = ""
    smtp_password: str = ""
    smtp_from:     str = "noreply@hipnuscosmeticos.com.br"

    # Frontend
    hipnus_api_url: str = "http://localhost:8000"


settings = Settings()
