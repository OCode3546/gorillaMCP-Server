"""Data model and persistence for __APP_TITLE__ (no UI code, so it is easy to test)."""

from __future__ import annotations

import json
import os
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


def default_data_path() -> Path:
    """Per-user data file: %APPDATA% on Windows, ~/Library/Application Support on macOS, XDG on Linux."""
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "__APP_NAME__" / "data.json"


@dataclass
class Item:
    title: str
    body: str = ""
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    updated: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


class Store:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_data_path()
        self.items: list[Item] = []
        self.load()

    def load(self) -> None:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.items = [Item(**entry) for entry in raw.get("items", [])]
        except (OSError, ValueError, TypeError):
            self.items = []

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"items": [asdict(i) for i in self.items]}, indent=2), encoding="utf-8")
        tmp.replace(self.path)  # atomic, so a crash never leaves a half-written file

    def add(self, title: str, body: str = "") -> Item:
        item = Item(title=title.strip() or "Untitled", body=body)
        self.items.insert(0, item)
        self.save()
        return item

    def update(self, item_id: str, title: str, body: str) -> Item:
        item = self.get(item_id)
        item.title = title.strip() or "Untitled"
        item.body = body
        item.updated = datetime.now().isoformat(timespec="seconds")
        self.save()
        return item

    def delete(self, item_id: str) -> None:
        self.items = [i for i in self.items if i.id != item_id]
        self.save()

    def get(self, item_id: str) -> Item:
        for item in self.items:
            if item.id == item_id:
                return item
        raise KeyError(item_id)

    def search(self, query: str) -> list[Item]:
        q = query.lower().strip()
        if not q:
            return list(self.items)
        return [i for i in self.items if q in i.title.lower() or q in i.body.lower()]
