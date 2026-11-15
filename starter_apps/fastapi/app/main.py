"""Servicio de ejemplo: punto de partida con un endpoint de salud y uno con validacion."""
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Servicio de ejemplo")


class Item(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    quantity: int = Field(ge=1, le=1000)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/items", status_code=201)
def create_item(item: Item) -> Item:
    return item
