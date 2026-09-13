from sqlalchemy import case, func
from sqlalchemy.orm import Session
from app.services import finance_service as f


def business_insights(db: Session, business_id: int, preset: str = "month") -> dict:
    """FR-32: significant sales changes, unusual expenses, demand shifts."""
    start, end = f.resolve_range(preset if preset in f.PRESETS else "month")
    profit = f.profit_summary(db, business_id, start, end)
    trend = f.sales_trend(db, business_id, start, end)
    top = f.top_products(db, business_id, start, end, limit=10)
    insights: list[dict] = []
    if trend:
        revs = [t["revenue"] for t in trend]
        if len(revs) >= 2 and revs[0] > 0:
            change = (revs[-1] - revs[0]) / revs[0] * 100
            if abs(change) >= 20:
                insights.append({"type": "sales_change",
                                 "title": "Sales up %.1f%% in period" % abs(change) if change > 0
                                 else "Sales down %.1f%% in period" % abs(change),
                                 "detail": "From %s to %s." % (revs[0], revs[-1])})
        peak = max(trend, key=lambda t: t["revenue"])
        insights.append({"type": "sales_peak", "title": "Peak sales day %s" % peak["period"],
                         "detail": "Revenue %s from %s order(s)." % (peak["revenue"], peak["orders"])})
    if profit["total_expenses"] > 0 and profit["net_revenue"] > 0:
        ratio = profit["total_expenses"] / profit["net_revenue"] * 100
        if ratio >= 30:
            insights.append({"type": "expense_watch",
                             "title": "Expenses are %.1f%% of revenue" % ratio,
                             "detail": "Expenses %s vs net revenue %s."
                             % (profit["total_expenses"], profit["net_revenue"])})
    if top:
        best = top[0]
        insights.append({"type": "demand",
                         "title": "Strong demand: %s" % best["product_name"],
                         "detail": "%s unit(s), revenue %s." % (best["quantity"], best["revenue"])})
        zeros = [r for r in top if r["quantity"] == 0]
        if zeros:
            names = ", ".join(str(r["product_name"]) for r in zeros[:5])
            insights.append({"type": "slow_mover",
                             "title": "%d product(s) with no sales" % len(zeros),
                             "detail": "Consider promotion or delisting: " + names})
    if profit["net_profit"] < 0:
        insights.append({"type": "loss", "title": "Business ran at a net loss",
                         "detail": "Net profit %s." % profit["net_profit"]})
    if not insights:
        insights.append({"type": "steady", "title": "No major anomalies",
                         "detail": "Sales, expenses and demand look stable."})
    return {"preset": preset, "profit": profit, "insights": insights}


def forecast_demand(db: Session, business_id: int, product_id: int | None = None,
                    days: int = 30) -> dict:
    """FR-33: moving-average forecast from last-30d net quantities sold.

    Aggregated in SQL (single GROUP BY) instead of hydrating Sale rows.
    """
    from app.models.product import Product
    from app.models.sales import Sale, SaleItem
    start, _ = f.resolve_range("month")
    net_qty = (SaleItem.quantity - func.coalesce(SaleItem.returned_qty, 0))
    agg = dict(db.query(
        SaleItem.product_id,
        func.sum(case((net_qty > 0, net_qty), else_=0)),
    ).join(Sale, Sale.id == SaleItem.sale_id).filter(
        Sale.business_id == business_id,
        Sale.status.in_(f.REVENUE_STATUSES),
        Sale.created_at >= start,
    ).group_by(SaleItem.product_id).all())
    q = db.query(Product.id, Product.name, Product.quantity_on_hand
                 ).filter(Product.business_id == business_id)
    if product_id is not None:
        q = q.filter(Product.id == product_id)
    out = []
    for pid, pname, on_hand in q.all():
        sold = int(agg.get(pid, 0) or 0)
        daily = sold / 30.0
        out.append({"product_id": pid, "product_name": pname,
                    "sold_last_30d": sold, "daily_rate": round(daily, 3),
                    "forecast_days": days, "predicted_demand": round(daily * days, 2),
                    "current_stock": on_hand or 0})
    out.sort(key=lambda r: r["predicted_demand"], reverse=True)
    return {"forecast_days": days, "products": out}
