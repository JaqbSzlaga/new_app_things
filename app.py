from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

from flask import Flask, jsonify, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "pantry.db"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["MAX_CONTENT_LENGTH"] = 6 * 1024 * 1024


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def db() -> sqlite3.Connection:
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS homes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                image_filename TEXT,
                created_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS inventory (
                home_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
                updated_at INTEGER NOT NULL,
                PRIMARY KEY(home_id, product_id),
                FOREIGN KEY(home_id) REFERENCES homes(id) ON DELETE CASCADE,
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS shopping_list (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL UNIQUE,
                wanted_quantity INTEGER NOT NULL DEFAULT 1 CHECK(wanted_quantity >= 1),
                checked INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL,
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
            );
            """
        )
        count = conn.execute("SELECT COUNT(*) AS c FROM homes").fetchone()["c"]
        if count == 0:
            now = int(time.time())
            conn.executemany(
                "INSERT INTO homes(name, created_at) VALUES(?, ?)",
                [("Dom 1", now), ("Dom 2", now)],
            )


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file) -> str | None:
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename):
        raise ValueError("Dozwolone formaty zdjęć: png, jpg, jpeg, webp, gif.")
    original = secure_filename(file.filename)
    ext = original.rsplit(".", 1)[1].lower()
    filename = f"{uuid4().hex}.{ext}"
    file.save(UPLOAD_DIR / filename)
    return filename


@app.before_request
def _init() -> None:
    init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/uploads/<path:filename>")
def uploaded_file(filename: str):
    return send_from_directory(UPLOAD_DIR, filename)


@app.get("/api/state")
def api_state():
    with db() as conn:
        homes = [row_to_dict(r) for r in conn.execute("SELECT * FROM homes ORDER BY id")]
        products = [row_to_dict(r) for r in conn.execute("SELECT * FROM products ORDER BY name COLLATE NOCASE")]
        inventory = [
            row_to_dict(r)
            for r in conn.execute(
                """
                SELECT h.id AS home_id, p.id AS product_id, COALESCE(i.quantity, 0) AS quantity
                FROM homes h
                CROSS JOIN products p
                LEFT JOIN inventory i ON i.home_id = h.id AND i.product_id = p.id
                ORDER BY h.id, p.name COLLATE NOCASE
                """
            )
        ]
        shopping = [
            row_to_dict(r)
            for r in conn.execute(
                """
                SELECT s.id, s.product_id, s.wanted_quantity, s.checked, p.name, p.image_filename
                FROM shopping_list s
                JOIN products p ON p.id = s.product_id
                ORDER BY s.checked ASC, p.name COLLATE NOCASE
                """
            )
        ]
    return jsonify({"homes": homes, "products": products, "inventory": inventory, "shopping": shopping})


@app.post("/api/homes")
def add_home():
    name = (request.form.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Podaj nazwę domu."}), 400
    try:
        with db() as conn:
            conn.execute("INSERT INTO homes(name, created_at) VALUES(?, ?)", (name, int(time.time())))
    except sqlite3.IntegrityError:
        return jsonify({"error": "Taki dom już istnieje."}), 400
    return redirect(url_for("index"))


@app.post("/api/products")
def add_product():
    name = (request.form.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Podaj nazwę produktu."}), 400
    try:
        image_filename = save_image(request.files.get("image"))
        with db() as conn:
            cur = conn.execute(
                "INSERT INTO products(name, image_filename, created_at) VALUES(?, ?, ?)",
                (name, image_filename, int(time.time())),
            )
            product_id = cur.lastrowid
            for home in conn.execute("SELECT id FROM homes"):
                qty = int(request.form.get(f"qty_home_{home['id']}") or 0)
                conn.execute(
                    "INSERT INTO inventory(home_id, product_id, quantity, updated_at) VALUES(?, ?, ?, ?)",
                    (home["id"], product_id, max(0, qty), int(time.time())),
                )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except sqlite3.IntegrityError:
        return jsonify({"error": "Taki produkt już istnieje."}), 400
    return redirect(url_for("index"))


@app.post("/api/products/<int:product_id>/delete")
def delete_product(product_id: int):
    with db() as conn:
        row = conn.execute("SELECT image_filename FROM products WHERE id = ?", (product_id,)).fetchone()
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    if row and row["image_filename"]:
        try:
            (UPLOAD_DIR / row["image_filename"]).unlink(missing_ok=True)
        except OSError:
            pass
    return jsonify({"ok": True})


@app.post("/api/homes/<int:home_id>/delete")
def delete_home(home_id: int):
    with db() as conn:
        conn.execute("DELETE FROM homes WHERE id = ?", (home_id,))
    return jsonify({"ok": True})


@app.post("/api/inventory/change")
def change_inventory():
    data = request.get_json(force=True)
    home_id = int(data.get("home_id"))
    product_id = int(data.get("product_id"))
    delta = int(data.get("delta"))
    add_to_shopping = bool(data.get("add_to_shopping", False))

    with db() as conn:
        current = conn.execute(
            "SELECT quantity FROM inventory WHERE home_id = ? AND product_id = ?",
            (home_id, product_id),
        ).fetchone()
        quantity = current["quantity"] if current else 0
        new_quantity = max(0, quantity + delta)
        conn.execute(
            """
            INSERT INTO inventory(home_id, product_id, quantity, updated_at)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(home_id, product_id)
            DO UPDATE SET quantity = excluded.quantity, updated_at = excluded.updated_at
            """,
            (home_id, product_id, new_quantity, int(time.time())),
        )
        if add_to_shopping:
            conn.execute(
                """
                INSERT INTO shopping_list(product_id, wanted_quantity, checked, created_at)
                VALUES(?, 1, 0, ?)
                ON CONFLICT(product_id)
                DO UPDATE SET wanted_quantity = shopping_list.wanted_quantity + 1, checked = 0
                """,
                (product_id, int(time.time())),
            )
    return jsonify({"ok": True, "quantity": new_quantity})


@app.post("/api/shopping/add")
def shopping_add():
    data = request.get_json(force=True)
    product_id = int(data.get("product_id"))
    with db() as conn:
        conn.execute(
            """
            INSERT INTO shopping_list(product_id, wanted_quantity, checked, created_at)
            VALUES(?, 1, 0, ?)
            ON CONFLICT(product_id)
            DO UPDATE SET wanted_quantity = shopping_list.wanted_quantity + 1, checked = 0
            """,
            (product_id, int(time.time())),
        )
    return jsonify({"ok": True})


@app.post("/api/shopping/<int:item_id>/change")
def shopping_change(item_id: int):
    data = request.get_json(force=True)
    delta = int(data.get("delta"))
    with db() as conn:
        row = conn.execute("SELECT wanted_quantity FROM shopping_list WHERE id = ?", (item_id,)).fetchone()
        if not row:
            return jsonify({"error": "Nie znaleziono pozycji."}), 404
        qty = row["wanted_quantity"] + delta
        if qty <= 0:
            conn.execute("DELETE FROM shopping_list WHERE id = ?", (item_id,))
        else:
            conn.execute("UPDATE shopping_list SET wanted_quantity = ? WHERE id = ?", (qty, item_id))
    return jsonify({"ok": True})


@app.post("/api/shopping/<int:item_id>/toggle")
def shopping_toggle(item_id: int):
    with db() as conn:
        conn.execute("UPDATE shopping_list SET checked = 1 - checked WHERE id = ?", (item_id,))
    return jsonify({"ok": True})


@app.post("/api/shopping/<int:item_id>/delete")
def shopping_delete(item_id: int):
    with db() as conn:
        conn.execute("DELETE FROM shopping_list WHERE id = ?", (item_id,))
    return jsonify({"ok": True})


@app.post("/api/shopping/clear_checked")
def shopping_clear_checked():
    with db() as conn:
        conn.execute("DELETE FROM shopping_list WHERE checked = 1")
    return jsonify({"ok": True})


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
