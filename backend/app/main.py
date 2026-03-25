"""
CapitalSense — FastAPI Application Factory
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db

# Routers
from app.routers import (
    auth,
    questionnaire,
    ocr,
    obligations,
    receivables,
    vendors,
    funds,
    dashboard,
    scenario,
    notifications,
    chatbot,
    email_draft,
)

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("Starting CapitalSense backend — env=%s", settings.APP_ENV)
    if settings.APP_ENV == "development":
        await init_db()   # auto-create tables in dev; use Alembic in prod
    yield
    logger.info("CapitalSense backend shutting down.")


app = FastAPI(
    title="CapitalSense API",
    description=(
        "Semi-autonomous cash flow decision intelligence backend "
        "for small businesses. Handles data, OCR, ML orchestration."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Lock down in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug("%s %s", request.method, request.url.path)
    response = await call_next(request)
    return response


# ── Global exception handler ──────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# ── Routers ───────────────────────────────────────────────────────────────────

API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(questionnaire.router, prefix=API_PREFIX)
app.include_router(ocr.router, prefix=API_PREFIX)
app.include_router(obligations.router, prefix=API_PREFIX)
app.include_router(receivables.router, prefix=API_PREFIX)
app.include_router(vendors.router, prefix=API_PREFIX)
app.include_router(funds.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)
app.include_router(scenario.router, prefix=API_PREFIX)
app.include_router(notifications.router, prefix=API_PREFIX)
app.include_router(chatbot.router, prefix=API_PREFIX)
app.include_router(email_draft.router, prefix=API_PREFIX)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}
