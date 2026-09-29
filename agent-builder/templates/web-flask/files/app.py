"""__APP_TITLE__ — Flask web app with a JSON API backed by SQLite.

Run: flask --app app run --debug
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from flask import Flask, abort, g, jsonify, render_template, request

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    done INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def create_app(db_path: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config["DATABASE"] = db_path or os.environ.get("DATABASE", str(Path(app.instance_path) / "app.db"))
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)

    def db() -> sqlite3.Connection:
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_exc: BaseException | None) -> None:
        conn = g.pop("db", None)
        if conn is not None:
            conn.close()

    with app.app_context():
        db().executescript(SCHEMA)

    def row_to_dict(row: sqlite3.Row) -> dict:
        item = dict(row)
        item["done"] = bool(item["done"])
        return item

    def get_item_or_404(item_id: int) -> sqlite3.Row:
        row = db().execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        if row is None:
            abort(404, description="Item not found")
        return row

    @app.get("/")
    def index():
        return render_template("index.html", title="__APP_TITLE__", description="__APP_DESCRIPTION__")

    @app.get("/api/items")
    def list_items():
        rows = db().execute("SELECT * FROM items ORDER BY done, id DESC").fetchall()
        return jsonify([row_to_dict(r) for r in rows])

    @app.post("/api/items")
    def create_item():
        data = request.get_json(silent=True) or {}
        title = str(data.get("title", "")).strip()
        if not title:
            return jsonify(error="title is required"), 400
        cur = db().execute("INSERT INTO items (title) VALUES (?)", (title,))
        db().commit()
        return jsonify(row_to_dict(get_item_or_404(cur.lastrowid))), 201

    @app.patch("/api/items/<int:item_id>")
    def update_item(item_id: int):
        get_item_or_404(item_id)
        data = request.get_json(silent=True) or {}
        if "title" in data:
            title = str(data["title"]).strip()
            if not title:
                return jsonify(error="title cannot be empty"), 400
            db().execute("UPDATE items SET title = ? WHERE id = ?", (title, item_id))
        if "done" in data:
            db().execute("UPDATE items SET done = ? WHERE id = ?", (int(bool(data["done"])), item_id))
        db().commit()
        return jsonify(row_to_dict(get_item_or_404(item_id)))

    @app.delete("/api/items/<int:item_id>")
    def delete_item(item_id: int):
        get_item_or_404(item_id)
        db().execute("DELETE FROM items WHERE id = ?", (item_id,))
        db().commit()
        return "", 204

    @app.errorhandler(404)
    def not_found(err):
        if request.path.startswith("/api/"):
            return jsonify(error=getattr(err, "description", "Not found")), 404
        return err

    return app


app = create_app()
