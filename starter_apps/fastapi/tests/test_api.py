import os

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repo import MemoryRepo, PgRepo, get_repo

BACKENDS = ["memory"] + (["postgres"] if os.environ.get("DATABASE_URL") else [])


@pytest.fixture(params=BACKENDS)
def client(request):
    """Cada prueba corre contra memoria y, si hay DATABASE_URL (CI), tambien contra Postgres real."""
    if request.param == "postgres":
        repo = PgRepo(os.environ["DATABASE_URL"])
        with repo.connect() as conn:
            conn.execute("TRUNCATE items RESTART IDENTITY")
    else:
        repo = MemoryRepo()
    app.dependency_overrides[get_repo] = lambda: repo
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_create_and_list_items(client):
    r = client.post("/items", json={"name": "cafe", "quantity": 2})
    assert r.status_code == 201
    assert r.json() == {"id": 1, "name": "cafe", "quantity": 2}
    assert client.get("/items").json() == [{"id": 1, "name": "cafe", "quantity": 2}]


def test_create_item_rejects_invalid_quantity(client):
    r = client.post("/items", json={"name": "cafe", "quantity": 0})
    assert r.status_code == 422
    assert client.get("/items").json() == []


def test_migrations_are_idempotent():
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("requiere DATABASE_URL")
    PgRepo(os.environ["DATABASE_URL"])
    PgRepo(os.environ["DATABASE_URL"])  # segunda vez: no debe fallar ni repetir migraciones
