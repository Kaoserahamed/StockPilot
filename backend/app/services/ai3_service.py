from sqlalchemy.orm import Session


def reorder_recommendations(db: Session, business_id: int, forecast_days: int = 30) -> dict:
    """FR-34: recommended qty = max(0, predicted + min_stock - on_hand)."""
    from app.models.product import Product
    from app.services.ai2_service import forecast_demand as _fc
    fc = _fc(db, business_id, days=forecast_days)
    pmap = {p.id: p for p in db.query(Product).filter(Product.business_id == business_id).all()}
    recs = []
    for row in fc["products"]:
        p = pmap.get(row["product_id"])
        if not p:
            continue
        need = (row["predicted_demand"] or 0) + (p.min_stock or 0) - (p.quantity_on_hand or 0)
        qty = max(0, int(round(need)))
        if qty == 0 and row["predicted_demand"] == 0:
            continue
        recs.append({**row, "min_stock": p.min_stock or 0,
                     "recommended_qty": qty, "needs_reorder": qty > 0,
                     "reason": "Predicted %s + min %s - on-hand %s"
                     % (row["predicted_demand"], p.min_stock, p.quantity_on_hand)})
    recs.sort(key=lambda r: (not r["needs_reorder"], -r["recommended_qty"]))
    return {"forecast_days": forecast_days, "recommendations": recs,
            "needs_reorder": [r for r in recs if r["needs_reorder"]]}


def detect_anomalies(db: Session, business_id: int) -> dict:
    """FR-35: z-score outliers on daily revenue + oversized single sales."""
    from sqlalchemy import func as _f
    from app.models.sales import Sale
    from app.services import finance_service as ff
    # Light: only what the algorithm needs (no full-row hydration).
    trend_rows = db.query(
        _f.date(Sale.created_at).label("d"),
        _f.count(Sale.id),
        _f.coalesce(_f.sum(Sale.total_amount), 0),
    ).filter(*ff._sale_range_filters(business_id, None, None)
             ).group_by(_f.date(Sale.created_at)).order_by(
        _f.date(Sale.created_at).asc()).all()
    trend = [{"period": str(d), "orders": int(o or 0), "revenue": float(r or 0)}
             for d, o, r in trend_rows]
    anomalies: list[dict] = []
    if len(trend) >= 4:
        revs = [t["revenue"] for t in trend]
        mean = sum(revs) / len(revs)
        var = sum((r - mean) ** 2 for r in revs) / len(revs)
        std = var ** 0.5
        if std > 0:
            for t in trend:
                z = (t["revenue"] - mean) / std
                if abs(z) >= 2:
                    anomalies.append({"type": "daily_revenue_outlier",
                                      "title": "Unusual daily revenue on %s" % t["period"],
                                      "detail": "Revenue %s (z=%.2f)." % (t["revenue"], z),
                                      "z": round(z, 2), "period": t["period"]})
    sale_rows = db.query(Sale.id, Sale.invoice_no, Sale.total_amount).filter(
        Sale.business_id == business_id, Sale.status.in_(ff.REVENUE_STATUSES)
    ).order_by(Sale.id.desc()).limit(ff.MAX_SALE_IDS).all()
    if sale_rows:
        totals = [s[2] or 0 for s in sale_rows]
        mean = sum(totals) / len(totals)
        for sid, inv, tot in [s for s in sale_rows if mean > 0 and (s[2] or 0) >= mean * 3][:5]:
            anomalies.append({"type": "large_sale",
                              "title": "Abnormally large sale %s" % inv,
                              "detail": "Total %s vs average %.2f." % (tot, mean),
                              "sale_id": sid, "invoice_no": inv})
    return {"anomalies": anomalies, "count": len(anomalies)}


def summarize_report(report_kind: str, report_data: dict) -> str:
    """FR-36: concise NL summary, flagged as insight not raw records."""
    tag = " (Insight - not raw records; verify against transactions.)"
    if report_kind == "profit":
        return ("Profit: net revenue %(net_revenue)s from %(orders)s order(s); "
                "COGS %(cogs)s; expenses %(total_expenses)s; gross %(gross_profit)s, "
                "net %(net_profit)s." % report_data) + tag
    if report_kind == "sales":
        s = report_data.get("summary", report_data)
        return ("Sales: %(orders)s order(s), gross %(gross_revenue)s, "
                "net %(net_revenue)s after refunds %(refunded)s." % s) + tag
    if report_kind == "expenses":
        s = report_data.get("summary", report_data)
        return ("Expenses total %(total_expenses)s across %(n)s record(s)."
                % {"total_expenses": s.get("total_expenses"),
                   "n": len(report_data.get("rows", []))}) + tag
    if report_kind == "inventory":
        s = report_data.get("summary", report_data)
        return ("Inventory: %(units)s unit(s) across %(skus)s SKU(s); cost %(cost_value)s, "
                "retail %(retail_value)s." % s) + tag
    return "Summary generated from the selected report." + tag
