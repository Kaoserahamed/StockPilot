"""Expense-related finance queries: summaries and breakdowns."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.finance import Expense


def expense_summary(db: Session, business_id: int, start, end) -> dict:
    """Total expenses for a period."""
    row = db.query(
        func.count(Expense.id),
        func.coalesce(func.sum(Expense.amount), 0),
    ).filter(Expense.business_id == business_id,
             *([Expense.expense_date >= start] if start is not None else []),
             *([Expense.expense_date <= end] if end is not None else []),
             ).first()
    return {"count": int(row[0] or 0), "total": float(row[1] or 0)}


def expense_breakdown(db: Session, business_id: int, start, end) -> list[dict]:
    """Expense totals grouped by category."""
    rows = db.query(
        Expense.category,
        func.count(Expense.id),
        func.coalesce(func.sum(Expense.amount), 0),
    ).filter(Expense.business_id == business_id,
             *([Expense.expense_date >= start] if start is not None else []),
             *([Expense.expense_date <= end] if end is not None else []),
             ).group_by(Expense.category).all()
    return [{"category": r[0], "count": int(r[1] or 0), "total": float(r[2] or 0)} for r in rows]
