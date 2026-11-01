"""FastAPI application entry point for NEXORA AICTE."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.database import init_db
from app.rate_limit import limiter
from app.routers import (
    admin, applications, audit, auth, compliance, dashboard, documents, evc,
    lease, notifications, reports, users, workflow,
)
from app.services.scheduler import scheduler, scheduled_monitor


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    if not scheduler.running:
        scheduler.add_job(scheduled_monitor, "interval", minutes=5, id="deadline-monitor",
                          replace_existing=True, max_instances=1)
        scheduler.start()
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="NEXORA AICTE API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.APP_ENV == "development" else None,
    redoc_url="/redoc" if settings.APP_ENV == "development" else None,
    openapi_url="/openapi.json" if settings.APP_ENV == "development" else None,
)
app.state.limiter = limiter


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if not (
            settings.APP_ENV == "development"
            and request.url.path in {"/docs", "/redoc"}
        ):
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
            )
        if request.url.scheme == "https":
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response


app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "nexora-aicte-backend", "db": "ok"}


for api_router in (
    auth.router, users.router, admin.router, applications.router, workflow.router,
    dashboard.router, documents.router, compliance.router, lease.router, evc.router,
    notifications.router, reports.router, audit.router,
):
    app.include_router(api_router)
