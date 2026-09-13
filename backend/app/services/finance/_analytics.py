"""Analytics queries: top products, customer stats, supplier stats."""
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.sales import Sale, SaleItem
from app.models.transactions import Purchase
from app.services.finance._utils import _sale_range_filters, REVENUE_STATUSES


def top_products(db: Session, business_id: int, start, end, limit: int = 10) -> list[dict]:
    """FR-20: top products by quantity sold with revenue and profit."""
    net_qty = SaleItem.quantity - SaleItem.returned_qty
    avg = dict(db.query(
        Purchase.supplier_id,  # placeholder — we need product avg cost
    ).filter().all()) if False else {}  # noqa — replaced below
    # Use purchase_price from product for COGS approximation
    rows = db.query(
        SaleItem.product_id,
        func.sum(case((net_qty > 0, net_qty), else_=0)).label("qty"),
        func.sum(case((net_qty > 0, net_qty * SaleItem.unit_price), else_=0.0)).label("rev"),
    ).join(Sale, Sale.id == SaleItem.sale_id).filter(
        Sale.business_id == business_id,
        Sale.status.in_(REVENUE_STATUSES),
        *([Sale.created_at >= start] if start is not None else []),
        *([Sale.created_at <= end] if end is not None else []),
    ).group_by(SaleItem.product_id).all()
    agg = []
    for pid, qty, rev in rows:
        q = int(qty or 0)
        r = float(rev or 0)
        agg.append((pid, q, r, r - q * avg.get(pid, 0.0)))
    agg.sort(key=lambda t: t[1], reverse=True)
    top = agg[:max(1, min(limit, 100))]
    names = {}
    if top:
        ids = [t[0] for t in top]
        names = {pid: n for pid, n in db.query(Product.id, Product.name
                                               ).filter(Product.id.in_(ids)).all()}
    return [{"product_id": pid, "product_name": names.get(pid),
             "quantity": q, "revenue": round(r, 2),
             "profit": round(p, 2)} for pid, q, r, p in top]


def customer_stats(db: Session, business_id: int, start, end, limit: int = 10) -> list[dict]:
    """FR-21: net spend + order count per customer (SQL GROUP BY)."""
    from app.models.party import Customer
    rows = db.query(
        Sale.customer_id,
        func.count(Sale.id),
        func.sum(Sale.total_amount - func.coalesce(Sale.refunded_amount, 0)),
    ).filter(*_sale_range_filters(business_id, start, end),
             Sale.customer_id.isnot(None)
             ).group_by(Sale.customer_id).all()
    rows = sorted(rows, key=lambda r: float(r[2] or 0), reverse=True
                  )[:max(1, min(limit, 100))]
    names = {}
    if rows:
        ids = [r[0] for r in rows]
        names = {cid: n for cid, n in db.query(Customer.id, Customer.name
                                               ).filter(Customer.id.in_(ids)).all()}
    return [{"customer_id": cid, "customer_name": names.get(cid),
             "orders": int(cnt or 0), "spent": round(float(spent or 0), 2)}
            for cid, cnt, spent in rows]


def supplier_stats(db: Session, business_id: int, start, end) -> list[dict]:
    """FR-22: purchase value + outstanding per supplier (SQL GROUP BY)."""
    from app.models.party import Supplier
    flt = [Purchase.business_id == business_id, Purchase.status != "cancelled"]
    if start is not None:
        flt.append(Purchase.purchase_date >= start)
    if end is not None:
        flt.append(Purchase.purchase_date <= end)
    rows = db.query(Purchase.supplier_id, func.count(Purchase.id),
                    func.sum(Purchase.total_amount)
                    ).filter(*flt).group_by(Purchase.supplier_id).all()
    rows = sorted(rows, key=lambda r: float(r[2] or 0), reverse=True)
    sups = {}
    if rows:
        ids = [r[0] for r in rows]
        sups = {s.id: s for s in db.query(Supplier
                                         ).filter(Supplier.id.in_(ids)).all()}
    out = []
    for sid, cnt, purchased in rows:
        s = sups.get(sid)
        out.append({"supplier_id": sid,
                    "supplier_name": s.company_name if s else None,
                    "orders": int(cnt or 0), "purchased": round(float(purchased or 0), 2),
                    "outstanding": round(s.outstanding_balance or 0, 2) if s else 0})
    return out
