"""__APP_TITLE__ — FastAPI service.

Run: uvicorn main:app --reload   (docs at http://127.0.0.1:8000/docs)
"""

from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock

from fastapi import FastAPI, HTTPException, status

from models import Item, ItemCreate, ItemUpdate

app = FastAPI(title="__APP_TITLE__", description="__APP_DESCRIPTION__", version="0.1.0")


class Repository:
    """In-memory storage. Replace with a database (e.g. SQLModel/SQLAlchemy) for persistence."""

    def __init__(self) -> None:
        self._items: dict[int, Item] = {}
        self._next_id = 1
        self._lock = Lock()

    def list(self) -> list[Item]:
        return list(self._items.values())

    def get(self, item_id: int) -> Item:
        try:
            return self._items[item_id]
        except KeyError:
            raise HTTPException(status_code=404, detail="Item not found") from None

    def create(self, data: ItemCreate) -> Item:
        with self._lock:
            item = Item(id=self._next_id, created_at=datetime.now(timezone.utc), **data.model_dump())
            self._items[item.id] = item
            self._next_id += 1
        return item

    def update(self, item_id: int, data: ItemUpdate) -> Item:
        item = self.get(item_id)
        updated = item.model_copy(update=data.model_dump(exclude_unset=True))
        self._items[item_id] = updated
        return updated

    def delete(self, item_id: int) -> None:
        self.get(item_id)
        del self._items[item_id]


repo = Repository()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/items", response_model=list[Item])
def list_items() -> list[Item]:
    return repo.list()


@app.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED)
def create_item(data: ItemCreate) -> Item:
    return repo.create(data)


@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int) -> Item:
    return repo.get(item_id)


@app.patch("/items/{item_id}", response_model=Item)
def update_item(item_id: int, data: ItemUpdate) -> Item:
    return repo.update(item_id, data)


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int) -> None:
    repo.delete(item_id)
