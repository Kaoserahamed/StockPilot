"""Revenue-related finance queries: summaries, trends, sales-in-range."""
from datetime import timedelta
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.finance import Expense
from app.models.sales import Sale, SaleItem
from app.services.finance._utils import (
    _memo_get, _memo_set, _sale_range_filters, MAX_SALE_IDS, MAX_TREND_BUCKETS,
    REVENUE_STATUSES,
)


def sales_in_range(db: Session, business_id: int, start, end):
    """Fetch sales rows for a period. Bounded + newest-first to prevent OOM."""
    q = db.query(Sale).filter(*_sale_range_filters(business_id, start, end))
    return q.order_by(Sale.id.desc()).limit(MAX_SALE_IDS).all()


def revenue_summary(db: Session, business_id: int, start, end) -> dict:
    """FR-16: gross/net revenue + order count for a period (single SQL query)."""
    hit = _memo_get(db, "revenue_summary", business_id, start, end)
    if hit is not None:
        return hit
    row = db.query(
        func.count(Sale.id),
        func.coalesce(func.sum(Sale.total_amount), 0),
        func.coalesce(func.sum(Sale.paid_amount), 0),
    ).filter(*_sale_range_filters(business_id, start, end)).first()
    expense = db.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).filter(Expense.business_id == business_id,
             *([Expense.expense_date >= start] if start is not None else []),
             *([Expense.expense_date <= end] if end is not None else []),
             ).scalar()
    result = {
        "orders": int(row[0] or 0),
        "revenue": float(row[1] or 0),
        "collected": float(row[2] or 0),
        "expenses": float(expense or 0),
        "net_profit": float(row[1] or 0) - float(expense or 0),
    }
    return _memo_set(db, "revenue_summary", business_id, start, end, result)


def revenue_trend(db: Session, business_id: int, start, end, bucket: str = "day") -> list[dict]:
    """FR-18: revenue trend grouped by day/week/month."""
    from app.services.finance._utils import MAX_TREND_BUCKETS
    if bucket == "month":
        fmt = "%Y-%m"
    elif bucket == "week":
        fmt = "%Y-W%W"
    else:
        fmt = "%Y-%m-%d"
    rows = db.query(
        func.date_format(Sale.created_at, fmt).label("period"),
        func.count(Sale.id),
        func.coalesce(func.sum(Sale.total_amount), 0),
    ).filter(*_sale_range_filters(business_id, start, end)
              ).group_by("period").order_by("period").limit(MAX_TREND_BUCKETS).all()
    return [{"period": r[0], "orders": int(r[1] or 0), "revenue": float(r[2] or 0)} for r in rows]
