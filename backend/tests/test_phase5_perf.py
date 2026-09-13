"""Phase-5 AI + analytics perf regression tests.

These exercise the SQL-aggregated code paths (finance_service rewrites and
ai2/ai3 service refactors) that Phase-1..3 tests don't touch.
"""
from tests.conftest import register_owner


def _seed_store(client, email="ai@test.com"):
    h = register_owner(client, email)
    s = client.post("/api/v1/suppliers", json={"company_name": "Big Agro"}, headers=h).json()
    p = client.post("/api/v1/products", json={
        "name": "Rice 1kg", "sku": "R-1", "selling_price": 100,
        "purchase_price": 60, "min_stock": 5}, headers=h).json()
    c = client.post("/api/v1/customers", json={"name": "Shop A"}, headers=h).json()
    client.post("/api/v1/purchases",
                json={"supplier_id": s["id"],
                      "items": [{"product_id": p["id"], "quantity": 40, "unit_cost": 60}]},
                headers=h)
    sale = client.post("/api/v1/sales/checkout",
                       json={"items": [{"product_id": p["id"], "quantity": 10}],
                             "customer_id": c["id"], "payment_method": "cash"},
                       headers=h).json()
    client.post("/api/v1/returns", json={
        "sale_id": sale["id"], "reason": "test",
        "items": [{"sale_item_id": sale["items"][0]["id"], "quantity": 1}]}, headers=h)
    client.post("/api/v1/expenses", json={"category": "rent", "amount": 90}, headers=h)
    return h, s, p, c, sale


def test_dashboard_math_with_returns(client):
    h, _, p, _, _ = _seed_store(client, "dash@test.com")
    r = client.get("/api/v1/dashboard?preset=all", headers=h)
    assert r.status_code == 200, r.text
    d = r.json()
    # gross 1000 - refund 100 = net 900; cogs 9*60=540; expenses 90
    assert d["revenue"] == 900 and d["gross_profit"] == 360, d
    assert d["net_profit"] == 270 and d["orders"] == 1, d
    assert d["top_products"][0]["quantity"] == 9
    assert len(d["sales_trend"]) >= 1

    r = client.get("/api/v1/finance/cogs?preset=all", headers=h)
    assert r.json()["total_cogs"] == 540, r.json()

    r = client.get("/api/v1/analytics/customers?preset=all", headers=h)
    top = r.json()["top_customers"]
    assert top and top[0]["spent"] == 900, r.json()

    r = client.get("/api/v1/analytics/suppliers?preset=all", headers=h)
    assert r.json()["suppliers"][0]["purchased"] == 2400, r.json()  # 40 * 60


def test_ai_forecast_reorder_anomalies(client):
    h, _, p, _, _ = _seed_store(client, "for@test.com")
    fc = client.get("/api/v1/ai/forecast?days=30", headers=h)
    assert fc.status_code == 200, fc.text
    prod = next(x for x in fc.json()["products"] if x["product_id"] == p["id"])
    assert prod["sold_last_30d"] == 9, prod
    assert prod["predicted_demand"] == 9, prod  # 9 sold -> 30-day forecast == 9

    rr = client.get("/api/v1/ai/reorder-recommendations?days=30", headers=h)
    assert rr.status_code == 200, rr.text
    # stock 31, sold 9, min 5 => forecast 9 + min 5 - on-hand 31 < 0 -> no reorder
    row = next(x for x in rr.json()["recommendations"] if x["product_id"] == p["id"])
    assert row["min_stock"] == 5 and row["needs_reorder"] is False, row

    an = client.get("/api/v1/ai/anomalies", headers=h)
    assert an.status_code == 200 and "anomalies" in an.json()

    ins = client.get("/api/v1/ai/insights?preset=all", headers=h)
    assert ins.status_code == 200 and ins.json()["insights"]

def test_dashboard_query_count_bounded(client):
    """Memoization keeps a dashboard request to a bounded number of SQL statements."""
    from sqlalchemy import event
    from app.db.session import get_db
    from app.main import app

    h, _, _, _, _ = _seed_store(client, "q@test.com")
    original = app.dependency_overrides.get(get_db)
    emitted: list[str] = []

    def _patched():
        db = next(original())
        setattr(db, "_fin_cache", {})
        conn = db.connection()

        def _probe(_c, _cur, _stmt, *_a, **_k):
            emitted.append(str(_stmt)[:50])

        event.listen(conn, "before_cursor_execute", _probe)
        try:
            yield db
        finally:
            event.remove(conn, "before_cursor_execute", _probe)
            db.close()

    app.dependency_overrides[get_db] = _patched
    try:
        r = client.get("/api/v1/dashboard?preset=all", headers=h)
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert r.status_code == 200, r.text
    assert emitted, "no SQL statements recorded"
    assert len(emitted) <= 30, f"dashboard issued {len(emitted)} queries: {emitted}"
