import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import analytics, auth, businesses, categories, employees, expenses, finance, inventory, invoices, parties, products, purchases, reports, returns, sales
from app.api.v1 import settings as settings_api
from app.api.v1 import subscription as subscription_api
from app.api.v1 import ai as ai_api
from app.api import health as health_api
from app.core.config import settings
from app.core.deps import Context, get_current_context
from app.core.exceptions import register_exception_handlers
from app.core.logging_config import setup_logging
from app.core.middleware import register_middleware
from app.core.csrf import CSRFMiddleware
from app.core.timeouts import setup_timeouts
from app.db.base import Base
from app.db.session import engine, ensure_indexes, get_db
import app.models  # noqa: F401 - register models

# Setup structured logging
setup_logging(level=settings.log_level, json_format=settings.json_logs)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # Startup
    logger.info("Starting %s (env=%s)", settings.app_name, settings.environment)
    # Phase-1 convenience; Alembic migrations take over in production.
    Base.metadata.create_all(bind=engine)
    ensure_indexes()
    logger.info("Database initialized and indexes ensured")

    yield

    # Shutdown
    logger.info("Shutting down %s", settings.app_name)
    engine.dispose()
    logger.info("Database connections closed")


@app.get("/", include_in_schema=False)
def root():
    """Root endpoint — returns basic API info."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1",
    }


app = FastAPI(title=settings.app_name, lifespan=lifespan,
    description="""
## StockPilot API - Inventory & POS SaaS

Multi-tenant inventory management, point-of-sale, finance tracking, and AI insights
for small businesses.

### Authentication
All API endpoints require a Bearer token in the Authorization header:
`Authorization: Bearer <access_token>`

Include the business ID in the X-Business-Id header:
`X-Business-Id: <business_id>`

### Rate Limiting
- Default: 100 requests per minute per user
- Auth endpoints: 5 requests per minute per IP

### Support
For issues and feature requests, contact support.
""",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

# --- CORS (environment-based) ---
if settings.cors_origins.strip() == "*":
    allowed_origins = ["*"]
else:
    allowed_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Custom middleware (security headers, request context) ---
register_middleware(app)

# --- Request timeouts ---
setup_timeouts(app)

# --- Exception handlers ---
register_exception_handlers(app)

# --- Health check endpoints ---
app.include_router(health_api.router)

# --- Audit logs endpoint ---
@app.get("/api/v1/audit-logs")
def list_audit_logs(ctx: Context = Depends(get_current_context), db=Depends(get_db)):
    if ctx.role not in ("Owner", "Manager"):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    from app.models.inventory import AuditLog
    rows = db.query(AuditLog).filter(AuditLog.business_id == ctx.business_id).order_by(
        AuditLog.id.desc()).limit(200).all()
    return [{"id": r.id, "user_id": r.user_id, "action": r.action, "resource": r.resource,
             "resource_id": r.resource_id, "old_value": r.old_value, "new_value": r.new_value,
             "created_at": r.created_at} for r in rows]


# --- API v1 routers ---
app.include_router(auth.router, prefix="/api/v1")
app.include_router(businesses.router, prefix="/api/v1")
app.include_router(employees.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(parties.router, prefix="/api/v1")
app.include_router(inventory.router, prefix="/api/v1")
app.include_router(purchases.router, prefix="/api/v1")
app.include_router(sales.router, prefix="/api/v1")
app.include_router(invoices.router, prefix="/api/v1")
app.include_router(returns.router, prefix="/api/v1")
app.include_router(expenses.router, prefix="/api/v1")
app.include_router(finance.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(settings_api.router, prefix="/api/v1")
app.include_router(subscription_api.router, prefix="/api/v1")
app.include_router(ai_api.router, prefix="/api/v1")
