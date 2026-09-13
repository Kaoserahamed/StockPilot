from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.deps import Context, get_current_context
from app.db.session import get_db
from app.models.product import Product
from app.services import finance_service as f

router = APIRouter(tags=["analytics"])


@router.get("/dashboard")
def dashboard(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db),
              preset: str = Query("month")):
    """FR-19: KPIs + sales trend + top products + stock alerts."""
    preset = preset if preset in f.PRESETS else "month"
    start, end = f.resolve_range(preset)
    profit = f.profit_summary(db, ctx.business_id, start, end)
    trend = f.sales_trend(db, ctx.business_id, start, end)
    top = f.top_products(db, ctx.business_id, start, end, limit=5)
    inv = f.inventory_value(db, ctx.business_id)
    low = db.query(Product).filter(
        Product.business_id == ctx.business_id, Product.is_active.is_(True),
        Product.quantity_on_hand > 0,
        Product.quantity_on_hand <= Product.min_stock).count()
    out = db.query(Product).filter(
        Product.business_id == ctx.business_id, Product.is_active.is_(True),
        Product.quantity_on_hand <= 0).count()
    return {"preset": preset, "total_sales": profit["gross_revenue"],
            "orders": profit["orders"], "revenue": profit["net_revenue"],
            "gross_profit": profit["gross_profit"], "net_profit": profit["net_profit"],
            "expenses": profit["total_expenses"], "cogs": profit["cogs"],
            "inventory": inv, "low_stock_count": low, "out_of_stock_count": out,
            "sales_trend": trend, "top_products": top}


@router.get("/analytics/products")
def product_perf(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db),
                 preset: str = Query("month"), date_from: datetime | None = None,
                 date_to: datetime | None = None, limit: int = Query(10, le=100)):
    """FR-20: product qty/revenue/profit, filterable by range."""
    preset = preset if preset in f.PRESETS else "month"
    start, end = f.resolve_range(preset, date_from, date_to)
    rows = f.top_products(db, ctx.business_id, start, end, limit=limit)
    return {"best_sellers": [r for r in rows if r["quantity"] > 0][:5],
            "low_performers": [r for r in rows if r["quantity"] == 0],
            "all": rows}


@router.get("/analytics/customers")
def customer_perf(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db),
                  preset: str = Query("month"), limit: int = Query(10, le=100)):
    """FR-21: top/returning customers by spend."""
    start, end = f.resolve_range(preset if preset in f.PRESETS else "month")
    rows = f.customer_stats(db, ctx.business_id, start, end, limit=limit)
    return {"top_customers": rows[:5],
            "returning": [r for r in rows if r["orders"] > 1], "all": rows}


@router.get("/analytics/suppliers")
def supplier_perf(ctx: Context = Depends(get_current_context), db: Session = Depends(get_db),
                  preset: str = Query("month"), date_from: datetime | None = None,
                  date_to: datetime | None = None):
    """FR-22: purchase value + outstanding per supplier."""
    preset = preset if preset in f.PRESETS else "month"
    start, end = f.resolve_range(preset, date_from, date_to)
    return {"suppliers": f.supplier_stats(db, ctx.business_id, start, end)}
