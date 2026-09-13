from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.deps import Context, get_current_context
from app.db.session import get_db
from app.services import finance_service as f

router = APIRouter(prefix="/finance", tags=["finance"])

PRESETS = ("today", "week", "month", "year", "custom", "all")


def _finance_guard(ctx: Context):
    """FR-25.4: financial data restricted to authorized roles."""
    if ctx.role not in ("Owner", "Manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")


@router.get("/revenue")
def revenue(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db),
            preset: str = Query("month"), date_from: datetime | None = None,
            date_to: datetime | None = None):
    """FR-16: revenue for a period + trend buckets."""
    _finance_guard(ctx)
    preset = preset if preset in PRESETS else "month"
    start, end = f.resolve_range(preset, date_from, date_to)
    out = f.revenue_summary(db, ctx.business_id, start, end)
    out["trend"] = f.sales_trend(db, ctx.business_id, start, end)
    out.update({"preset": preset})
    return out


@router.get("/cogs")
def cogs(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db),
         preset: str = Query("month"), date_from: datetime | None = None,
         date_to: datetime | None = None):
    """FR-17: COGS overall + per product."""
    _finance_guard(ctx)
    preset = preset if preset in PRESETS else "month"
    start, end = f.resolve_range(preset, date_from, date_to)
    return f.cogs_summary(db, ctx.business_id, start, end)


@router.get("/profit")
def profit(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db),
           preset: str = Query("month"), date_from: datetime | None = None,
           date_to: datetime | None = None):
    """FR-18: gross/net profit for a period."""
    _finance_guard(ctx)
    preset = preset if preset in PRESETS else "month"
    start, end = f.resolve_range(preset, date_from, date_to)
    return f.profit_summary(db, ctx.business_id, start, end)
