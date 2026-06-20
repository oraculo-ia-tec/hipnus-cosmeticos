"""
main.py — HIPNUS COSMÉTICOS
==============================
Entrypoint da API FastAPI.

Startup:
  1. Cria todas as tabelas no banco (create_all).
  2. Executa seed_super_admin para garantir que o admin padrão exista.

Rotas registradas:
  /health              — healthcheck público
  /api/v1/auth         — autenticação e usuários
  /api/v1/catalog      — catálogo de produtos
  /api/v1/orders       — pedidos
  /api/v1/stores       — lojas parceiras
  /api/v1/payments     — pagamentos Asaas
  /api/v1/invites      — convites de cadastro
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import Base, engine, SessionLocal
from app.db.registry import import_all_models
from app.domains.users.service import seed_super_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    import_all_models()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_super_admin(db)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
def health():
    """Healthcheck público. Usado pelo frontend para verificar se a API está no ar."""
    return {"status": "ok", "app": settings.app_name}


# ─── Routers ────────────────────────────────────────────────────────────────
from app.domains.users.router import router as auth_router
app.include_router(auth_router, prefix="/api/v1")

try:
    from app.domains.catalog.router import router as catalog_router
    app.include_router(catalog_router, prefix="/api/v1")
except ImportError:
    pass

try:
    from app.domains.orders.router import router as orders_router
    app.include_router(orders_router, prefix="/api/v1")
except ImportError:
    pass

try:
    from app.domains.stores.router import router as stores_router
    app.include_router(stores_router, prefix="/api/v1")
except ImportError:
    pass

try:
    from app.domains.payments.router import router as payments_router
    app.include_router(payments_router, prefix="/api/v1")
except ImportError:
    pass

try:
    from app.domains.invites.router import router as invites_router
    app.include_router(invites_router, prefix="/api/v1")
except ImportError:
    pass
