"""Missing finance aggregates (part 1): trends + profit + inventory."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.finance import Expense
from app.models.sales import Sale, SaleItem
from app.services.finance._utils import _memo_get, _memo_set, _sale_range_filters


def revenue_trend_alias(db, business_id, start, end, bucket="day"):
    from app.services.finance._revenue import revenue_trend as _rt
    return _rt(db, business_id, start, end, bucket=bucket)


def sales_trend(db: Session, business_id: int, start, end) -> list[dict]:
    period = func.to_char(Sale.created_at, "YYYY-MM-DD").label("period")
    rows = db.query(period, func.count(Sale.id),
                    func.coalesce(func.sum(Sale.total_amount), 0)
                    ).filter(*_sale_range_filters(business_id, start, end)
                             ).group_by(period).order_by(period).all()
    return [{"period": str(r[0]), "orders": int(r[1] or 0),
             "revenue": float(r[2] or 0)} for r in rows]


def _cogs_total(db: Session, business_id: int, start, end) -> float:
    from app.models.product import Product
    expr = func.coalesce(func.sum(
        (SaleItem.quantity - func.coalesce(SaleItem.returned_qty, 0))
        * func.coalesce(Product.purchase_price, 0.0)), 0)
    val = db.query(expr).select_from(SaleItem).join(
        Sale, Sale.id == SaleItem.sale_id).join(
        Product, Product.id == SaleItem.product_id).filter(
        *_sale_range_filters(business_id, start, end)).scalar()
    return float(val or 0)


def profit_summary(db: Session, business_id: int, start, end) -> dict:
    hit = _memo_get(db, "profit_summary", business_id, start, end)
    if hit is not None:
        return hit
    rev = db.query(func.count(Sale.id),
                   func.coalesce(func.sum(Sale.total_amount), 0),
                   func.coalesce(func.sum(Sale.refunded_amount), 0),
                   ).filter(*_sale_range_filters(business_id, start, end)).first()
    orders = int(rev[0] or 0)
    gross = float(rev[1] or 0)
    refunded = float(rev[2] or 0)
    net = round(gross - refunded, 2)
    exp = float(db.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.business_id == business_id,
        *([Expense.expense_date >= start] if start is not None else []),
        *([Expense.expense_date <= end] if end is not None else []),
    ).scalar() or 0)
    cogs = round(_cogs_total(db, business_id, start, end), 2)
    gross_p = round(net - cogs, 2)
    net_p = round(gross_p - exp, 2)
    result = {"orders": orders, "gross_revenue": round(gross, 2),
              "refunded": round(refunded, 2), "net_revenue": net,
              "cogs": cogs, "total_expenses": round(exp, 2),
              "gross_profit": gross_p, "net_profit": net_p,
              "revenue": net, "expenses": round(exp, 2)}
    return _memo_set(db, "profit_summary", business_id, start, end, result)


def inventory_value(db: Session, business_id: int) -> dict:
    from app.models.product import Product
    row = db.query(func.count(Product.id),
                   func.coalesce(func.sum(Product.quantity_on_hand), 0),
                   func.coalesce(func.sum(
                       Product.quantity_on_hand * Product.purchase_price), 0),
                   func.coalesce(func.sum(
                       Product.quantity_on_hand * Product.selling_price), 0),
                   ).filter(Product.business_id == business_id,
                            Product.is_active.is_(True)).first()
    return {"skus": int(row[0] or 0), "units": int(row[1] or 0),
            "cost_value": round(float(row[2] or 0), 2),
            "retail_value": round(float(row[3] or 0), 2)}


def expenses_total(db: Session, business_id: int, start, end) -> dict:
    row = db.query(func.count(Expense.id),
                   func.coalesce(func.sum(Expense.amount), 0),
                   ).filter(Expense.business_id == business_id,
                            *([Expense.expense_date >= start]
                              if start is not None else []),
                            *([Expense.expense_date <= end]
                              if end is not None else []),
                            ).first()
    return {"count": int(row[0] or 0), "total": float(row[1] or 0),
            "total_expenses": float(row[1] or 0)}


def cogs_summary(db: Session, business_id: int, start, end) -> dict:
    from app.models.product import Product
    total = round(_cogs_total(db, business_id, start, end), 2)
    per = (SaleItem.quantity - func.coalesce(SaleItem.returned_qty, 0))
    rows = db.query(SaleItem.product_id,
                    func.coalesce(func.sum(
                        per * func.coalesce(Product.purchase_price, 0.0)), 0),
                    func.coalesce(func.sum(SaleItem.quantity), 0),
                    ).select_from(SaleItem).join(
        Sale, Sale.id == SaleItem.sale_id).join(
        Product, Product.id == SaleItem.product_id).filter(
        *_sale_range_filters(business_id, start, end)
    ).group_by(SaleItem.product_id).all()
    names = {}
    if rows:
        ids = [r[0] for r in rows]
        names = {pid: n for pid, n in db.query(
            Product.id, Product.name).filter(Product.id.in_(ids)).all()}
    items = [{"product_id": r[0], "product_name": names.get(r[0]),
              "quantity": int(r[2] or 0), "cogs": round(float(r[1] or 0), 2)}
             for r in sorted(rows, key=lambda r: float(r[1] or 0),
                             reverse=True)]
    return {"total_cogs": total, "cogs": total, "products": items}


def avg_costs(db: Session, business_id: int) -> dict:
    from app.models.transactions import Purchase, PurchaseItem
    rows = db.query(PurchaseItem.product_id,
                    func.coalesce(func.avg(PurchaseItem.unit_cost), 0),
                    ).join(Purchase, Purchase.id == PurchaseItem.purchase_id
                           ).filter(Purchase.business_id == business_id
                                    ).group_by(PurchaseItem.product_id).all()
    return {int(pid): float(avg or 0) for pid, avg in rows}
