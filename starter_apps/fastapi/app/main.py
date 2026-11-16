"""Servicio de ejemplo: salud, validacion y persistencia (Postgres si hay DATABASE_URL)."""
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

from app.repo import MemoryRepo, PgRepo, get_repo


@asynccontextmanager
async def lifespan(_app: FastAPI):
    get_repo()  # conecta y aplica las migraciones al arrancar, no en la primera peticion
    yield


app = FastAPI(title="Servicio de ejemplo", lifespan=lifespan)
Repo = Annotated[MemoryRepo | PgRepo, Depends(get_repo)]


class ItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    quantity: int = Field(ge=1, le=1000)


class Item(ItemIn):
    id: int


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/items", status_code=201)
def create_item(item: ItemIn, repo: Repo) -> Item:
    return Item(**repo.add(item.name, item.quantity))


@app.get("/items")
def list_items(repo: Repo) -> list[Item]:
    return [Item(**row) for row in repo.list()]
