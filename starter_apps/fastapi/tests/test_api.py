from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_create_item():
    r = client.post("/items", json={"name": "cafe", "quantity": 2})
    assert r.status_code == 201
    assert r.json() == {"name": "cafe", "quantity": 2}


def test_create_item_rejects_invalid_quantity():
    r = client.post("/items", json={"name": "cafe", "quantity": 0})
    assert r.status_code == 422
