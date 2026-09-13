"""Product activate/deactivate round-trip tests."""
from tests.conftest import register_owner


def _seed(client, email="act@test.com"):
    h = register_owner(client, email)
    p = client.post("/api/v1/products", json={"name": "Rice", "sku": "R-1"}, headers=h).json()
    return h, p


def test_deactivate_then_activate_roundtrip(client):
    h, p = _seed(client)
    assert p["is_active"] is True

    # deactivate
    r = client.post(f"/api/v1/products/{p['id']}/deactivate", headers=h)
    assert r.status_code == 200 and r.json()["is_active"] is False, r.text

    # deactivated product is hidden from POS search
    r = client.get("/api/v1/pos/search?q=Rice", headers=h)
    assert all(x["id"] != p["id"] for x in r.json()), r.text

    # activate again — previously impossible
    r = client.post(f"/api/v1/products/{p['id']}/activate", headers=h)
    assert r.status_code == 200 and r.json()["is_active"] is True, r.text

    # visible in POS search again
    r = client.get("/api/v1/pos/search?q=Rice", headers=h)
    assert any(x["id"] == p["id"] for x in r.json()), r.text


def test_activate_is_idempotent(client):
    h, p = _seed(client, "act2@test.com")
    # activating an already-active product is fine (no error)
    r = client.post(f"/api/v1/products/{p['id']}/activate", headers=h)
    assert r.status_code == 200 and r.json()["is_active"] is True, r.text


def test_activate_cashier_blocked(client):
    h, p = _seed(client, "act3@test.com")
    r = client.post("/api/v1/employees", json={
        "name": "Cash", "email": "cash-act@t.com", "password": "secret123",
        "role": "Cashier"}, headers=h)
    assert r.status_code == 201, r.text
    r = client.post("/api/v1/auth/login",
                    json={"username": "cash-act@t.com", "password": "secret123"})
    assert r.status_code == 200, r.text
    ch = {"Authorization": f"Bearer {r.json()['access_token']}"}
    for op in ("activate", "deactivate"):
        r = client.post(f"/api/v1/products/{p['id']}/{op}", headers=ch)
        assert r.status_code == 403, r.text


def test_activate_cross_business_blocked(client):
    h1, p = _seed(client, "act4@test.com")
    h2 = register_owner(client, "act5@test.com")
    client.post(f"/api/v1/products/{p['id']}/deactivate", headers=h1)
    r = client.post(f"/api/v1/products/{p['id']}/activate", headers=h2)
    assert r.status_code == 404, r.text


def test_activate_audited(client):
    h, p = _seed(client, "act6@test.com")
    client.post(f"/api/v1/products/{p['id']}/deactivate", headers=h)
    client.post(f"/api/v1/products/{p['id']}/activate", headers=h)
    r = client.get("/api/v1/audit-logs", headers=h)
    actions = [a["action"] for a in r.json()]
    assert "product.deactivate" in actions and "product.activate" in actions, r.text