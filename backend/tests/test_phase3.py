from tests.conftest import register_owner


def _seed(client):
    """Purchase 10 @60, sell 2 then 1 @100 => net qty 3, stock 7."""
    h = register_owner(client, "fin@test.com")
    sup = client.post("/api/v1/suppliers", json={"company_name": "S"}, headers=h).json()
    prod = client.post("/api/v1/products",
                       json={"name": "Rice", "sku": "R1", "selling_price": 100}, headers=h).json()
    cust = client.post("/api/v1/customers", json={"name": "C"}, headers=h).json()
    r = client.post("/api/v1/purchases", json={
        "supplier_id": sup["id"],
        "items": [{"product_id": prod["id"], "quantity": 10, "unit_cost": 60}]}, headers=h)
    assert r.status_code == 201, r.text
    s1 = client.post("/api/v1/sales/checkout",
                     json={"items": [{"product_id": prod["id"], "quantity": 2}],
                           "customer_id": cust["id"]}, headers=h).json()
    s2 = client.post("/api/v1/sales/checkout",
                     json={"items": [{"product_id": prod["id"], "quantity": 1}]}, headers=h).json()
    client.post("/api/v1/expenses", json={"category": "rent", "amount": 50}, headers=h)
    return h, prod, cust, s1, s2


def test_expense_crud(client):
    h = register_owner(client, "exp@test.com")
    r = client.post("/api/v1/expenses", json={"category": "rent", "amount": 100,
                                              "payment_method": "cash"}, headers=h)
    assert r.status_code == 201, r.text
    eid = r.json()["id"]
    r = client.post("/api/v1/expenses", json={"category": "bogus", "amount": 5}, headers=h)
    assert r.status_code == 422
    r = client.patch(f"/api/v1/expenses/{eid}", json={"amount": 120}, headers=h)
    assert r.status_code == 200 and r.json()["amount"] == 120
    r = client.get("/api/v1/expenses?category=rent", headers=h)
    assert r.status_code == 200 and len(r.json()) == 1
    assert client.delete(f"/api/v1/expenses/{eid}", headers=h).status_code == 204


def test_revenue_cogs_profit(client):
    h, prod, cust, s1, s2 = _seed(client)
    r = client.get("/api/v1/finance/revenue?preset=all", headers=h)
    body = r.json()
    assert body["orders"] == 2 and body["gross_revenue"] == 300, body
    assert len(body["trend"]) >= 1
    r = client.get("/api/v1/finance/cogs?preset=all", headers=h)
    assert r.json()["total_cogs"] == 180, r.json()  # 3 x 60
    assert str(prod["id"]) in r.json()["by_product"]
    r = client.get("/api/v1/finance/profit?preset=all", headers=h)
    p = r.json()
    assert p["net_revenue"] == 300 and p["gross_profit"] == 120, p
    assert p["total_expenses"] == 50 and p["net_profit"] == 70, p


def test_dashboard_analytics_reports(client):
    h, prod, cust, s1, s2 = _seed(client)
    r = client.get("/api/v1/dashboard?preset=all", headers=h)
    d = r.json()
    # revenue 300, cogs 180, expenses 50 -> gross 120, net 70
    assert d["revenue"] == 300 and d["net_profit"] == 70, d
    assert d["gross_profit"] == 120 and d["expenses"] == 50
    assert d["orders"] == 2 and d["inventory"]["units"] == 7
    assert d["top_products"][0]["product_name"] == "Rice"
    assert len(d["sales_trend"]) >= 1
    # FR-20 product performance
    r = client.get("/api/v1/analytics/products?preset=all", headers=h).json()
    assert r["all"][0]["quantity"] == 3 and r["all"][0]["revenue"] == 300
    assert r["all"][0]["profit"] == 120
    # FR-21 customers: C spent 200 (sale s1), walk-in sale s2 has no customer
    r = client.get("/api/v1/analytics/customers?preset=all", headers=h).json()
    assert r["top_customers"][0]["spent"] == 200, r
    # FR-22 suppliers
    r = client.get("/api/v1/analytics/suppliers?preset=all", headers=h).json()
    assert r["suppliers"][0]["purchased"] == 600, r
    assert r["suppliers"][0]["outstanding"] == 600
    # FR-23 reports: json + csv + pdf
    assert client.get("/api/v1/reports/sales?preset=all", headers=h).json()["summary"]["orders"] == 2
    r = client.get("/api/v1/reports/sales?preset=all&format=csv", headers=h)
    assert r.status_code == 200 and "invoice_no" in r.text
    r = client.get("/api/v1/reports/inventory", headers=h)
    assert r.json()["summary"]["units"] == 7
    r = client.get("/api/v1/reports/expenses?preset=all", headers=h)
    assert r.json()["summary"]["total_expenses"] == 50
    r = client.get("/api/v1/reports/profit?preset=all", headers=h)
    assert r.json()["net_profit"] == 70
    r = client.get("/api/v1/reports/profit/pdf?preset=all", headers=h)
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"
