from tests.conftest import register_owner


def test_full_phase1_workflow(client):
    h = register_owner(client)

    # business me
    r = client.get("/api/v1/businesses/me", headers=h)
    assert r.status_code == 200, r.text

    # category
    r = client.post("/api/v1/categories", json={"name": "Grocery"}, headers=h)
    assert r.status_code == 201, r.text
    cat_id = r.json()["id"]

    # product
    r = client.post("/api/v1/products", json={
        "name": "Rice 1kg", "sku": "RICE-001", "barcode": "12345",
        "category_id": cat_id, "brand": "ACI", "purchase_price": 60,
        "selling_price": 75, "min_stock": 10}, headers=h)
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # duplicate SKU blocked FR-5.7
    r = client.post("/api/v1/products", json={"name": "Dup", "sku": "RICE-001"}, headers=h)
    assert r.status_code == 409, r.text

    # search FR-5.6
    r = client.get("/api/v1/products?q=RICE", headers=h)
    assert r.status_code == 200 and len(r.json()) == 1

    # delete category blocked FR-4.4
    r = client.delete(f"/api/v1/categories/{cat_id}", headers=h)
    assert r.status_code == 400, r.text

    # inventory adjust +100 then -95 => low stock
    r = client.post("/api/v1/inventory/adjust",
                    json={"product_id": pid, "quantity_change": 100, "reason": "opening stock"}, headers=h)
    assert r.status_code == 201, r.text
    r = client.post("/api/v1/inventory/adjust",
                    json={"product_id": pid, "quantity_change": -95, "reason": "damaged"}, headers=h)
    assert r.status_code == 201, r.text

    r = client.get("/api/v1/inventory/low-stock", headers=h)
    assert r.status_code == 200 and len(r.json()) == 1

    r = client.get("/api/v1/inventory/transactions?product_id=" + str(pid), headers=h)
    assert r.status_code == 200 and len(r.json()) == 2

    # unauthenticated blocked FR-1.6
    r = client.get("/api/v1/products")
    assert r.status_code == 401


def test_cross_business_blocked(client):
    h1 = register_owner(client, "a@test.com")
    h2 = register_owner(client, "b@test.com")
    # product of A not visible to B
    r = client.post("/api/v1/products", json={"name": "X", "sku": "X-1"}, headers=h1)
    pid = r.json()["id"]
    r = client.get(f"/api/v1/products/{pid}", headers=h2)
    assert r.status_code == 404  # isolated, not leaked
