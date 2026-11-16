"""Almacenamiento de items. Con DATABASE_URL usa Postgres; sin ella, memoria (util para desarrollo y pruebas)."""
import os
from functools import lru_cache
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

MIGRATIONS = Path(__file__).parent / "migrations"


class MemoryRepo:
    def __init__(self) -> None:
        self._items: list[dict] = []

    def add(self, name: str, quantity: int) -> dict:
        item = {"id": len(self._items) + 1, "name": name, "quantity": quantity}
        self._items.append(item)
        return item

    def list(self) -> list[dict]:
        return list(self._items)


class PgRepo:
    def __init__(self, url: str) -> None:
        self.url = url
        self.migrate()

    def connect(self) -> psycopg.Connection:
        return psycopg.connect(self.url, row_factory=dict_row)

    def migrate(self) -> None:
        """Aplica migrations/*.sql en orden, una sola vez cada una. El lock evita carreras entre replicas."""
        with self.connect() as conn:
            conn.execute("SELECT pg_advisory_xact_lock(727274)")
            conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY)")
            done = {r["name"] for r in conn.execute("SELECT name FROM schema_migrations")}
            for path in sorted(MIGRATIONS.glob("*.sql")):
                if path.name not in done:
                    conn.execute(path.read_text(encoding="utf-8"))
                    conn.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (path.name,))

    def add(self, name: str, quantity: int) -> dict:
        with self.connect() as conn:
            return conn.execute(
                "INSERT INTO items (name, quantity) VALUES (%s, %s) RETURNING id, name, quantity",
                (name, quantity),
            ).fetchone()

    def list(self) -> list[dict]:
        with self.connect() as conn:
            return conn.execute("SELECT id, name, quantity FROM items ORDER BY id").fetchall()


@lru_cache
def get_repo() -> MemoryRepo | PgRepo:
    url = os.environ.get("DATABASE_URL")
    return PgRepo(url) if url else MemoryRepo()
