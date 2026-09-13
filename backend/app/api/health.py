"""Health check endpoints for StockPilot backend.

Provides:
- GET /health       - basic liveness probe
- GET /health/ready - readiness probe (DB connectivity)
- GET /health/detailed - full dependency status
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db, engine

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """Liveness probe - always returns 200 if the process is running."""
    return {"status": "ok", "service": "stockpilot-api"}


@router.get("/health/ready")
def health_ready(db: Session = Depends(get_db)) -> dict:
    """Readiness probe - verifies database connectivity."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": db_status},
        )
    return {"status": "ready", "database": db_status}


@router.get("/health/detailed")
def health_detailed(db: Session = Depends(get_db)) -> dict:
    """Detailed health status including all dependencies."""
    checks: dict = {"database": "unknown"}

    # Database check
    try:
        result = db.execute(text("SELECT 1"))
        row = result.scalar()
        checks["database"] = "connected" if row == 1 else "error"
    except Exception as exc:
        checks["database"] = f"error: {type(exc).__name__}"

    # Overall status
    all_ok = all(v == "connected" for v in checks.values())
    checks["status"] = "healthy" if all_ok else "degraded"

    return checks
