"""Price adjustment (inventory) endpoint tests."""
from tests.conftest import register_owner


def _seed(client, email="pa@test.com"):
    h = register_owner(client, email)
    p = client.post("/api/v1/products", json={
        "name": "Rice", "sku": "R-1", "purchase_price": 60,
        "selling_price": 100}, headers=h).json()
    return h, p


def test_adjust_price_updates_product_and_history(client):
    h, p = _seed(client)
    r = client.post("/api/v1/inventory/adjust-price", json={
        "product_id": p["id"], "new_selling_price": 120,
        "new_purchase_price": 70, "reason": "supplier hike"}, headers=h)
    assert r.status_code == 201, r.text
    row = r.json()
    assert row["old_selling_price"] == 100 and row["new_selling_price"] == 120
    assert row["old_purchase_price"] == 60 and row["new_purchase_price"] == 70

    # product reflects new prices
    r = client.get(f"/api/v1/products/{p['id']}", headers=h)
    assert r.json()["selling_price"] == 120 and r.json()["purchase_price"] == 70

    # history endpoint returns the row
    r = client.get("/api/v1/inventory/price-adjustments", headers=h)
    assert r.status_code == 200 and len(r.json()) == 1
    assert r.json()[0]["reason"] == "supplier hike"

    # filtered by product
    r = client.get(f"/api/v1/inventory/price-adjustments?product_id={p['id']}", headers=h)
    assert len(r.json()) == 1


def test_adjust_price_sell_only_keeps_cost(client):
    h, p = _seed(client, "pa2@test.com")
    r = client.post("/api/v1/inventory/adjust-price", json={
        "product_id": p["id"], "new_selling_price": 90, "reason": "promo"}, headers=h)
    assert r.status_code == 201, r.text
    row = r.json()
    assert row["new_selling_price"] == 90
    assert row["old_purchase_price"] == 60 and row["new_purchase_price"] == 60  # untouched
    assert client.get(f"/api/v1/products/{p['id']}", headers=h).json()["purchase_price"] == 60


def test_adjust_price_validation(client):
    h, p = _seed(client, "pa3@test.com")
    # no prices provided -> 422
    r = client.post("/api/v1/inventory/adjust-price", json={
        "product_id": p["id"], "reason": "x"}, headers=h)
    assert r.status_code == 422, r.text
    # unchanged prices -> 422
    r = client.post("/api/v1/inventory/adjust-price", json={
        "product_id": p["id"], "new_selling_price": 100, "reason": "same"}, headers=h)
    assert r.status_code == 422, r.text
    # unknown product -> 404
    r = client.post("/api/v1/inventory/adjust-price", json={
        "product_id": 99999, "new_selling_price": 5, "reason": "x"}, headers=h)
    assert r.status_code == 404, r.text
    # negative price -> 422 (schema ge=0)
    r = client.post("/api/v1/inventory/adjust-price", json={
        "product_id": p["id"], "new_selling_price": -1, "reason": "x"}, headers=h)
    assert r.status_code == 422, r.text


def test_adjust_price_cashier_blocked(client):
    h, p = _seed(client, "pa4@test.com")
    # owner creates a cashier
    r = client.post("/api/v1/employees", json={
        "name": "Cash", "email": "cash@t.com", "password": "secret123",
        "role": "Cashier"}, headers=h)
    assert r.status_code == 201, r.text
    # login as cashier
    r = client.post("/api/v1/auth/login", json={"username": "cash@t.com", "password": "secret123"})
    assert r.status_code == 200, r.text
    ch = {"Authorization": f"Bearer {r.json()['access_token']}"}
    r = client.post("/api/v1/inventory/adjust-price", json={
        "product_id": p["id"], "new_selling_price": 5, "reason": "x"}, headers=ch)
    assert r.status_code == 403, r.text


def test_adjust_price_cross_business_blocked(client):
    h1, p = _seed(client, "pa5@test.com")
    h2 = register_owner(client, "pa6@test.com")
    r = client.post("/api/v1/inventory/adjust-price", json={
        "product_id": p["id"], "new_selling_price": 5, "reason": "x"}, headers=h2)
    assert r.status_code == 404, r.text  # not leaked across businesses


def test_audit_log_records_price_change(client):
    h, p = _seed(client, "pa7@test.com")
    client.post("/api/v1/inventory/adjust-price", json={
        "product_id": p["id"], "new_selling_price": 150, "reason": "audit test"}, headers=h)
    r = client.get("/api/v1/audit-logs", headers=h)
    actions = [a["action"] for a in r.json()]
    assert "product.price_change" in actions, r.text