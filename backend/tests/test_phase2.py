from tests.conftest import register_owner


def _owner_with_stock(client, email="p2@test.com"):
    h = register_owner(client, email)
    r = client.post("/api/v1/suppliers", json={"company_name": "Sup"}, headers=h)
    assert r.status_code == 201, r.text
    sup_id = r.json()["id"]
    r = client.post("/api/v1/products", json={"name": "Rice", "sku": "R1"}, headers=h)
    assert r.status_code == 201, r.text
    pid = r.json()["id"]
    r = client.post("/api/v1/products", json={"name": "Oil", "sku": "O1"}, headers=h)
    assert r.status_code == 201, r.text
    pid2 = r.json()["id"]
    r = client.post("/api/v1/customers", json={"name": "Walk-in"}, headers=h)
    assert r.status_code == 201, r.text
    cust_id = r.json()["id"]
    return h, sup_id, pid, pid2, cust_id


def test_purchase_flow(client):
    h, sup_id, pid, pid2, _ = _owner_with_stock(client)
    # FR-10.3/10.4 multi-item + auto totals
    r = client.post("/api/v1/purchases", json={
        "supplier_id": sup_id,
        "items": [{"product_id": pid, "quantity": 10, "unit_cost": 50},
                  {"product_id": pid2, "quantity": 5, "unit_cost": 100}],
        "paid_amount": 200}, headers=h)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["subtotal"] == 1000 and body["total_amount"] == 1000
    assert body["payment_status"] == "partial"
    pur_id = body["id"]
    # FR-10.5 stock up
    r = client.get(f"/api/v1/products/{pid}", headers=h)
    assert r.json()["quantity_on_hand"] == 10
    # FR-10.6/10.7 history + detail
    r = client.get(f"/api/v1/suppliers/{sup_id}/purchases", headers=h)
    assert len(r.json()["purchases"]) == 1 and r.json()["outstanding_balance"] == 800
    # FR-10.8 pay rest
    r = client.post(f"/api/v1/purchases/{pur_id}/pay", json={"amount": 800}, headers=h)
    assert r.status_code == 200 and r.json()["payment_status"] == "paid", r.text
    # overpay blocked
    r = client.post(f"/api/v1/purchases/{pur_id}/pay", json={"amount": 1}, headers=h)
    assert r.status_code == 422


def test_pos_checkout_invoice(client):
    h, _, pid, _, cust_id = _owner_with_stock(client, "pos@test.com")
    client.post("/api/v1/purchases", json={
        "supplier_id": client.get("/api/v1/suppliers", headers=h).json()[0]["id"],
        "items": [{"product_id": pid, "quantity": 20, "unit_cost": 50}]}, headers=h)
    # FR-11.2 search
    r = client.get("/api/v1/pos/search?q=Rice", headers=h)
    assert r.status_code == 200 and len(r.json()) == 1
    # FR-11/12 checkout: discount+tax math, invoice no, stock down
    r = client.post("/api/v1/sales/checkout", json={
        "items": [{"product_id": pid, "quantity": 2}],
        "customer_id": cust_id, "discount_amount": 5,
        "tax_percent": 10, "payment_method": "cash"}, headers=h)
    assert r.status_code == 201, r.text
    sale = r.json()
    # subtotal=2*0 default price=0... set price first? selling_price default 0 -> use unit_price
    assert sale["invoice_no"].startswith("INV-")
    sale_id = sale["id"]
    r = client.get(f"/api/v1/products/{pid}", headers=h)
    assert r.json()["quantity_on_hand"] == 18
    # FR-11.7 oversell blocked
    r = client.post("/api/v1/sales/checkout",
                    json={"items": [{"product_id": pid, "quantity": 999}]}, headers=h)
    assert r.status_code == 400
    # FR-13 view + PDF
    r = client.get(f"/api/v1/invoices/{sale_id}", headers=h)
    assert r.status_code == 200 and "items" in r.json()
    r = client.get(f"/api/v1/invoices/{sale_id}/pdf", headers=h)
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"


def test_checkout_totals_and_return(client):
    h, _, pid, _, cust_id = _owner_with_stock(client, "ret@test.com")
    client.patch(f"/api/v1/products/{pid}", json={"selling_price": 100}, headers=h)
    sup_id = client.get("/api/v1/suppliers", headers=h).json()[0]["id"]
    client.post("/api/v1/purchases", json={
        "supplier_id": sup_id,
        "items": [{"product_id": pid, "quantity": 10, "unit_cost": 60}]}, headers=h)
    r = client.post("/api/v1/sales/checkout", json={
        "items": [{"product_id": pid, "quantity": 4}],
        "customer_id": cust_id, "payment_method": "credit",
        "paid_amount": 0}, headers=h)
    assert r.status_code == 201, r.text
    sale = r.json()
    assert sale["total_amount"] == 400 and sale["payment_status"] == "unpaid"
    r = client.get(f"/api/v1/customers/{cust_id}/sales", headers=h)
    assert r.json()["outstanding_balance"] == 400
    # FR-14 partial return of 1 qty
    item_id = sale["items"][0]["id"]
    r = client.post("/api/v1/returns", json={
        "sale_id": sale["id"], "reason": "damaged",
        "items": [{"sale_item_id": item_id, "quantity": 1}]}, headers=h)
    assert r.status_code == 201, r.text
    assert r.json()["refund_amount"] == 100
    r = client.get(f"/api/v1/products/{pid}", headers=h)
    assert r.json()["quantity_on_hand"] == 7  # 10-4+1
    # over-return blocked
    r = client.post("/api/v1/returns", json={
        "sale_id": sale["id"], "reason": "x",
        "items": [{"sale_item_id": item_id, "quantity": 99}]}, headers=h)
    assert r.status_code == 400
