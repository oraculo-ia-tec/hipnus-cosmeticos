"""
Aplicação FastAPI — HIPNUS COSMÉTICOS (marketplace de parceiros).

Monta a API modular por domínios:
- /api/v1/catalog   -> produtos oficiais Hipnus
- /api/v1/partners  -> onboarding de parceiros + subconta Asaas
- /api/v1/stores    -> lojas e ofertas dos parceiros
- /api/v1/payments  -> webhooks Asaas

Tratamento de erros de domínio mapeado para respostas HTTP coerentes.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import DomainError
from app.db import registry  # noqa: F401  (registra models)
from app.db.base import Base, engine
from app.domains.catalog.routers.products import router as catalog_router
from app.domains.partners.routers.partners import router as partners_router
from app.domains.payments.routers.webhooks import router as payments_router
from app.domains.stores.routers.stores import router as stores_router

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "Marketplace proprietário Hipnus Cosméticos. Cada parceiro possui uma "
        "loja com os produtos oficiais da marca, com split de pagamento via "
        "API oficial do Asaas."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """Cria as tabelas no startup (SQLite local). Em produção, usar migrations."""
    Base.metadata.create_all(bind=engine)


@app.exception_handler(DomainError)
async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    """Converte erros de domínio em respostas HTTP coerentes."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/health", tags=["Infra"])
def health() -> dict:
    """Healthcheck simples para monitoramento/infra."""
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}


P = settings.API_V1_PREFIX
app.include_router(catalog_router, prefix=P)
app.include_router(partners_router, prefix=P)
app.include_router(stores_router, prefix=P)
app.include_router(payments_router, prefix=P)
