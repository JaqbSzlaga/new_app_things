from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

from flask import Flask, jsonify, redirect, render_template, request, send_file, send_from_directory, url_for
from werkzeug.utils import secure_filename

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except Exception:  # local SQLite mode can work without psycopg2
    psycopg2 = None
    RealDictCursor = None

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "pantry.db"
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
USE_POSTGRES = bool(DATABASE_URL and DATABASE_URL.startswith(("postgres://", "postgresql://")))
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["MAX_CONTENT_LENGTH"] = 6 * 1024 * 1024

PRESET_PRODUCTS = [
    {'category': 'Podstawowe', 'name': 'Mleko', 'image_url': '/static/products/mleko.svg'},
    {'category': 'Podstawowe', 'name': 'Jajka', 'image_url': '/static/products/jajka.svg'},
    {'category': 'Podstawowe', 'name': 'Chleb', 'image_url': '/static/products/chleb.svg'},
    {'category': 'Podstawowe', 'name': 'Masło', 'image_url': '/static/products/maso.svg'},
    {'category': 'Podstawowe', 'name': 'Ser', 'image_url': '/static/products/ser.svg'},
    {'category': 'Podstawowe', 'name': 'Makaron', 'image_url': '/static/products/makaron.svg'},
    {'category': 'Podstawowe', 'name': 'Ryż', 'image_url': '/static/products/ryz.svg'},
    {'category': 'Podstawowe', 'name': 'Cukier', 'image_url': '/static/products/cukier.svg'},
    {'category': 'Podstawowe', 'name': 'Kawa', 'image_url': '/static/products/kawa.svg'},
    {'category': 'Podstawowe', 'name': 'Woda', 'image_url': '/static/products/woda.svg'},
    {'category': 'Podstawowe', 'name': 'Mąka', 'image_url': '/static/products/maka.svg'},
    {'category': 'Podstawowe', 'name': 'Sól', 'image_url': '/static/products/sol.svg'},
    {'category': 'Warzywa', 'name': 'Ziemniaki', 'image_url': '/static/products/ziemniaki.svg'},
    {'category': 'Warzywa', 'name': 'Marchew', 'image_url': '/static/products/marchew.svg'},
    {'category': 'Warzywa', 'name': 'Cebula', 'image_url': '/static/products/cebula.svg'},
    {'category': 'Warzywa', 'name': 'Czosnek', 'image_url': '/static/products/czosnek.svg'},
    {'category': 'Warzywa', 'name': 'Pomidor', 'image_url': '/static/products/pomidor.svg'},
    {'category': 'Warzywa', 'name': 'Ogórek', 'image_url': '/static/products/ogorek.svg'},
    {'category': 'Warzywa', 'name': 'Papryka', 'image_url': '/static/products/papryka.svg'},
    {'category': 'Warzywa', 'name': 'Sałata', 'image_url': '/static/products/saata.svg'},
    {'category': 'Owoce', 'name': 'Jabłka', 'image_url': '/static/products/jabka.svg'},
    {'category': 'Owoce', 'name': 'Banany', 'image_url': '/static/products/banany.svg'},
    {'category': 'Owoce', 'name': 'Pomarańcze', 'image_url': '/static/products/pomarancze.svg'},
    {'category': 'Owoce', 'name': 'Cytryny', 'image_url': '/static/products/cytryny.svg'},
    {'category': 'Owoce', 'name': 'Winogrona', 'image_url': '/static/products/winogrona.svg'},
    {'category': 'Owoce', 'name': 'Truskawki', 'image_url': '/static/products/truskawki.svg'},
    {'category': 'Mięso i ryby', 'name': 'Kurczak', 'image_url': '/static/products/kurczak.svg'},
    {'category': 'Mięso i ryby', 'name': 'Wołowina', 'image_url': '/static/products/woowina.svg'},
    {'category': 'Mięso i ryby', 'name': 'Wieprzowina', 'image_url': '/static/products/wieprzowina.svg'},
    {'category': 'Mięso i ryby', 'name': 'Mięso mielone', 'image_url': '/static/products/mieso-mielone.svg'},
    {'category': 'Mięso i ryby', 'name': 'Szynka', 'image_url': '/static/products/szynka.svg'},
    {'category': 'Nabiał', 'name': 'Jogurt', 'image_url': '/static/products/jogurt.svg'},
    {'category': 'Nabiał', 'name': 'Kefir', 'image_url': '/static/products/kefir.svg'},
    {'category': 'Nabiał', 'name': 'Twaróg', 'image_url': '/static/products/twarog.svg'},
    {'category': 'Nabiał', 'name': 'Mozzarella', 'image_url': '/static/products/mozzarella.svg'},
    {'category': 'Nabiał', 'name': 'Serek wiejski', 'image_url': '/static/products/serek-wiejski.svg'},
    {'category': 'Nabiał', 'name': 'Serek kanapkowy', 'image_url': '/static/products/serek-kanapkowy.svg'},
    {'category': 'Słodycze', 'name': 'Czekolada', 'image_url': '/static/products/czekolada.svg'},
    {'category': 'Słodycze', 'name': 'Batoniki', 'image_url': '/static/products/batoniki.svg'},
    {'category': 'Słodycze', 'name': 'Ciastka', 'image_url': '/static/products/ciastka.svg'},
    {'category': 'Słodycze', 'name': 'Wafelki', 'image_url': '/static/products/wafelki.svg'},
    {'category': 'Słodycze', 'name': 'Żelki', 'image_url': '/static/products/zelki.svg'},
    {'category': 'Przekąski słone', 'name': 'Chipsy', 'image_url': '/static/products/chipsy.svg'},
    {'category': 'Przekąski słone', 'name': 'Paluszki', 'image_url': '/static/products/paluszki.svg'},
    {'category': 'Przekąski słone', 'name': 'Krakersy', 'image_url': '/static/products/krakersy.svg'},
    {'category': 'Przekąski słone', 'name': 'Orzeszki', 'image_url': '/static/products/orzeszki.svg'},
    {'category': 'Przekąski słone', 'name': 'Popcorn', 'image_url': '/static/products/popcorn.svg'},
    {'category': 'Napoje', 'name': 'Sok jabłkowy', 'image_url': '/static/products/sok-jabkowy.svg'},
    {'category': 'Napoje', 'name': 'Sok pomarańczowy', 'image_url': '/static/products/sok-pomaranczowy.svg'},
    {'category': 'Napoje', 'name': 'Cola', 'image_url': '/static/products/cola.svg'},
    {'category': 'Napoje', 'name': 'Napój gazowany', 'image_url': '/static/products/napoj-gazowany.svg'},
    {'category': 'Napoje', 'name': 'Woda gazowana', 'image_url': '/static/products/woda-gazowana.svg'},
    {'category': 'Mrożonki', 'name': 'Pizza mrożona', 'image_url': '/static/products/pizza-mrozona.svg'},
    {'category': 'Mrożonki', 'name': 'Frytki', 'image_url': '/static/products/frytki.svg'},
    {'category': 'Mrożonki', 'name': 'Warzywa mrożone', 'image_url': '/static/products/warzywa-mrozone.svg'},
    {'category': 'Mrożonki', 'name': 'Owoce mrożone', 'image_url': '/static/products/owoce-mrozone.svg'},
    {'category': 'Chemia i dom', 'name': 'Papier toaletowy', 'image_url': '/static/products/papier-toaletowy.svg'},
    {'category': 'Chemia i dom', 'name': 'Ręcznik papierowy', 'image_url': '/static/products/recznik-papierowy.svg'},
    {'category': 'Chemia i dom', 'name': 'Płyn do naczyń', 'image_url': '/static/products/pyn-do-naczyn.svg'},
    {'category': 'Chemia i dom', 'name': 'Tabletki do zmywarki', 'image_url': '/static/products/tabletki-do-zmywarki.svg'}
]


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def connect():
    if USE_POSTGRES:
        if psycopg2 is None:
            raise RuntimeError("Brakuje psycopg2-binary. Sprawdź requirements.txt.")
        return psycopg2.connect(DATABASE_URL, sslmode="require", cursor_factory=RealDictCursor)
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def sql_params(sql: str) -> str:
    if USE_POSTGRES:
        return sql.replace("?", "%s").replace("COLLATE NOCASE", "")
    return sql


def fetch_all(conn, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    cur = conn.cursor()
    cur.execute(sql_params(sql), params)
    rows = cur.fetchall()
    return [dict(r) for r in rows]


def fetch_one(conn, sql: str, params: tuple = ()) -> dict[str, Any] | None:
    cur = conn.cursor()
    cur.execute(sql_params(sql), params)
    row = cur.fetchone()
    return dict(row) if row else None


def run(conn, sql: str, params: tuple = ()) -> None:
    cur = conn.cursor()
    cur.execute(sql_params(sql), params)


def run_many(conn, sql: str, params_list: list[tuple]) -> None:
    cur = conn.cursor()
    cur.executemany(sql_params(sql), params_list)


def insert_and_get_id(conn, sql: str, params: tuple = ()) -> int:
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute(sql_params(sql + " RETURNING id"), params)
        return int(cur.fetchone()["id"])
    cur.execute(sql, params)
    return int(cur.lastrowid)


def commit_or_rollback(conn, ok: bool) -> None:
    try:
        if ok:
            conn.commit()
        else:
            conn.rollback()
    finally:
        conn.close()


def init_db() -> None:
    conn = connect()
    ok = False
    try:
        cur = conn.cursor()
        if USE_POSTGRES:
            statements = [
                """
                CREATE TABLE IF NOT EXISTS homes (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    created_at INTEGER NOT NULL
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    image_filename TEXT,
                    image_url TEXT,
                    image_mime TEXT,
                    image_data BYTEA,
                    created_at INTEGER NOT NULL
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS inventory (
                    home_id INTEGER NOT NULL REFERENCES homes(id) ON DELETE CASCADE,
                    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                    quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
                    updated_at INTEGER NOT NULL,
                    PRIMARY KEY(home_id, product_id)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS shopping_list (
                    id SERIAL PRIMARY KEY,
                    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                    home_id INTEGER NOT NULL REFERENCES homes(id) ON DELETE CASCADE,
                    wanted_quantity INTEGER NOT NULL DEFAULT 1 CHECK(wanted_quantity >= 1),
                    checked INTEGER NOT NULL DEFAULT 0,
                    created_at INTEGER NOT NULL,
                    UNIQUE(product_id, home_id)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS notes (
                    id SERIAL PRIMARY KEY,
                    body TEXT NOT NULL,
                    done INTEGER NOT NULL DEFAULT 0,
                    created_at INTEGER NOT NULL
                )
                """,
            ]
        else:
            statements = [
                """
                CREATE TABLE IF NOT EXISTS homes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    created_at INTEGER NOT NULL
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    image_filename TEXT,
                    image_url TEXT,
                    image_mime TEXT,
                    image_data BLOB,
                    created_at INTEGER NOT NULL
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS inventory (
                    home_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
                    updated_at INTEGER NOT NULL,
                    PRIMARY KEY(home_id, product_id),
                    FOREIGN KEY(home_id) REFERENCES homes(id) ON DELETE CASCADE,
                    FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS shopping_list (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    home_id INTEGER NOT NULL,
                    wanted_quantity INTEGER NOT NULL DEFAULT 1 CHECK(wanted_quantity >= 1),
                    checked INTEGER NOT NULL DEFAULT 0,
                    created_at INTEGER NOT NULL,
                    FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE,
                    FOREIGN KEY(home_id) REFERENCES homes(id) ON DELETE CASCADE,
                    UNIQUE(product_id, home_id)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    body TEXT NOT NULL,
                    done INTEGER NOT NULL DEFAULT 0,
                    created_at INTEGER NOT NULL
                )
                """,
            ]
        for statement in statements:
            cur.execute(statement)
        count = fetch_one(conn, "SELECT COUNT(*) AS c FROM homes")["c"]
        if count == 0:
            now = int(time.time())
            run_many(conn, "INSERT INTO homes(name, created_at) VALUES(?, ?)", [("Dom 1", now), ("Dom 2", now)])
        ok = True
    finally:
        commit_or_rollback(conn, ok)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def read_image_upload(file) -> tuple[str | None, bytes | None]:
    if not file or not file.filename:
        return None, None
    if not allowed_file(file.filename):
        raise ValueError("Dozwolone formaty zdjęć: png, jpg, jpeg, webp, gif.")
    return file.mimetype or "application/octet-stream", file.read()


def save_image_to_file(file) -> str | None:
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename):
        raise ValueError("Dozwolone formaty zdjęć: png, jpg, jpeg, webp, gif.")
    original = secure_filename(file.filename)
    ext = original.rsplit(".", 1)[1].lower()
    filename = f"{uuid4().hex}.{ext}"
    file.save(UPLOAD_DIR / filename)
    return filename


def valid_preset_url(url: str | None) -> str | None:
    if not url:
        return None
    return url if any(item["image_url"] == url for item in PRESET_PRODUCTS) else None


def decorate_products(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for row in rows:
        if row.get("image_mime"):
            # On shopping rows, row["id"] is the shopping-list id, so use product_id for image route.
            image_product_id = row.get("product_id") or row.get("id")
            row["image_url"] = url_for("product_db_image", product_id=image_product_id)
        row.pop("image_data", None)
    return rows


@app.before_request
def _init() -> None:
    init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/uploads/<path:filename>")
def uploaded_file(filename: str):
    return send_from_directory(UPLOAD_DIR, filename)


@app.get("/api/products/<int:product_id>/image")
def product_db_image(product_id: int):
    conn = connect()
    try:
        row = fetch_one(conn, "SELECT image_mime, image_data FROM products WHERE id = ?", (product_id,))
    finally:
        conn.close()
    if not row or not row.get("image_data"):
        return "", 404
    from io import BytesIO
    data = row["image_data"]
    if isinstance(data, memoryview):
        data = data.tobytes()
    return send_file(BytesIO(data), mimetype=row.get("image_mime") or "application/octet-stream")


@app.get("/manifest.webmanifest")
def manifest():
    return send_from_directory(BASE_DIR / "static", "manifest.webmanifest")


@app.get("/service-worker.js")
def service_worker():
    return send_from_directory(BASE_DIR / "static", "service-worker.js")


@app.get("/api/state")
def api_state():
    conn = connect()
    try:
        homes = fetch_all(conn, "SELECT * FROM homes ORDER BY id")
        products = decorate_products(fetch_all(conn, "SELECT id, name, image_filename, image_url, image_mime, created_at FROM products ORDER BY name COLLATE NOCASE"))
        inventory = fetch_all(conn, """
            SELECT h.id AS home_id, p.id AS product_id, COALESCE(i.quantity, 0) AS quantity
            FROM homes h
            CROSS JOIN products p
            LEFT JOIN inventory i ON i.home_id = h.id AND i.product_id = p.id
            ORDER BY h.id, p.name COLLATE NOCASE
        """)
        shopping = decorate_products(fetch_all(conn, """
            SELECT s.id, s.product_id, s.home_id, s.wanted_quantity, s.checked,
                   p.name, p.image_filename, p.image_url, p.image_mime,
                   COALESCE(h.name, 'Ogólne') AS home_name
            FROM shopping_list s
            JOIN products p ON p.id = s.product_id
            LEFT JOIN homes h ON h.id = s.home_id
            ORDER BY s.checked ASC, h.name COLLATE NOCASE, p.name COLLATE NOCASE
        """))
        notes = fetch_all(conn, "SELECT * FROM notes ORDER BY done ASC, created_at DESC")
    finally:
        conn.close()
    categories = []
    for item in PRESET_PRODUCTS:
        if item["category"] not in categories:
            categories.append(item["category"])
    return jsonify({"homes": homes, "products": products, "inventory": inventory, "shopping": shopping, "notes": notes, "presets": PRESET_PRODUCTS, "preset_categories": categories})


@app.post("/api/homes")
def add_home():
    name = (request.form.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Podaj nazwę domu."}), 400
    conn = connect()
    ok = False
    try:
        run(conn, "INSERT INTO homes(name, created_at) VALUES(?, ?)", (name, int(time.time())))
        ok = True
    except Exception:
        return jsonify({"error": "Taki dom już istnieje."}), 400
    finally:
        commit_or_rollback(conn, ok)
    return redirect(url_for("index"))


@app.post("/api/products")
def add_product():
    name = (request.form.get("name") or "").strip()
    preset_url = valid_preset_url(request.form.get("preset_image_url"))
    if not name:
        return jsonify({"error": "Podaj nazwę produktu."}), 400
    conn = connect()
    ok = False
    try:
        image_file = request.files.get("image")
        image_filename = None
        image_mime = None
        image_data = None
        if USE_POSTGRES:
            image_mime, image_data = read_image_upload(image_file)
        else:
            image_filename = save_image_to_file(image_file)
        image_url = None if (image_filename or image_data) else preset_url
        product_id = insert_and_get_id(conn,
            "INSERT INTO products(name, image_filename, image_url, image_mime, image_data, created_at) VALUES(?, ?, ?, ?, ?, ?)",
            (name, image_filename, image_url, image_mime, image_data, int(time.time())),
        )
        for home in fetch_all(conn, "SELECT id FROM homes"):
            qty = int(request.form.get(f"qty_home_{home['id']}") or 0)
            run(conn, "INSERT INTO inventory(home_id, product_id, quantity, updated_at) VALUES(?, ?, ?, ?)", (home["id"], product_id, max(0, qty), int(time.time())))
        ok = True
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        return jsonify({"error": "Taki produkt już istnieje albo wystąpił błąd bazy."}), 400
    finally:
        commit_or_rollback(conn, ok)
    return redirect(url_for("index"))


@app.post("/api/products/bulk")
def add_products_bulk():
    data = request.get_json(force=True) or {}
    products = data.get("products") or []
    qty_by_home = data.get("qty_by_home") or {}
    if not products:
        return jsonify({"error": "Nie wybrano produktów."}), 400
    conn = connect()
    ok = False
    created = 0
    try:
        homes = [row["id"] for row in fetch_all(conn, "SELECT id FROM homes")]
        for item in products:
            name = (item.get("name") or "").strip()
            if not name:
                continue
            image_url = valid_preset_url(item.get("image_url"))
            existing = fetch_one(conn, "SELECT id FROM products WHERE lower(name) = lower(?)", (name,))
            if existing:
                product_id = existing["id"]
                if image_url:
                    run(conn, "UPDATE products SET image_url = COALESCE(image_url, ?) WHERE id = ?", (image_url, product_id))
            else:
                product_id = insert_and_get_id(conn, "INSERT INTO products(name, image_filename, image_url, image_mime, image_data, created_at) VALUES(?, NULL, ?, NULL, NULL, ?)", (name, image_url, int(time.time())))
                created += 1
            for home_id in homes:
                try:
                    qty = int(qty_by_home.get(str(home_id), qty_by_home.get(home_id, 0)) or 0)
                except (TypeError, ValueError):
                    qty = 0
                run(conn, """
                    INSERT INTO inventory(home_id, product_id, quantity, updated_at)
                    VALUES(?, ?, ?, ?)
                    ON CONFLICT(home_id, product_id)
                    DO UPDATE SET quantity = excluded.quantity, updated_at = excluded.updated_at
                """, (home_id, product_id, max(0, qty), int(time.time())))
        ok = True
    finally:
        commit_or_rollback(conn, ok)
    return jsonify({"ok": True, "created": created})


@app.post("/api/products/<int:product_id>/delete")
def delete_product(product_id: int):
    conn = connect()
    ok = False
    row = None
    try:
        row = fetch_one(conn, "SELECT image_filename FROM products WHERE id = ?", (product_id,))
        run(conn, "DELETE FROM products WHERE id = ?", (product_id,))
        ok = True
    finally:
        commit_or_rollback(conn, ok)
    if row and row.get("image_filename"):
        try:
            (UPLOAD_DIR / row["image_filename"]).unlink(missing_ok=True)
        except OSError:
            pass
    return jsonify({"ok": True})




@app.post("/api/homes/<int:home_id>/rename")
def rename_home(home_id: int):
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"ok": False, "error": "Nazwa domu nie może być pusta."}), 400
    conn = connect()
    ok = False
    try:
        run(conn, "UPDATE homes SET name = ? WHERE id = ?", (name, home_id))
        ok = True
        return jsonify({"ok": True})
    finally:
        commit_or_rollback(conn, ok)

@app.post("/api/homes/<int:home_id>/delete")
def delete_home(home_id: int):
    conn = connect()
    ok = False
    try:
        run(conn, "DELETE FROM homes WHERE id = ?", (home_id,))
        ok = True
    finally:
        commit_or_rollback(conn, ok)
    return jsonify({"ok": True})


def add_shopping_item(conn, product_id: int, home_id: int | None, amount: int = 1) -> None:
    run(conn, """
        INSERT INTO shopping_list(product_id, home_id, wanted_quantity, checked, created_at)
        VALUES(?, ?, ?, 0, ?)
        ON CONFLICT(product_id, home_id)
        DO UPDATE SET wanted_quantity = shopping_list.wanted_quantity + excluded.wanted_quantity, checked = 0
    """, (product_id, home_id, max(1, amount), int(time.time())))


@app.post("/api/inventory/change")
def change_inventory():
    data = request.get_json(force=True)
    home_id = int(data.get("home_id"))
    product_id = int(data.get("product_id"))
    delta = int(data.get("delta"))
    add_to_shopping = bool(data.get("add_to_shopping", False))
    conn = connect()
    ok = False
    try:
        current = fetch_one(conn, "SELECT quantity FROM inventory WHERE home_id = ? AND product_id = ?", (home_id, product_id))
        quantity = current["quantity"] if current else 0
        new_quantity = max(0, quantity + delta)
        run(conn, """
            INSERT INTO inventory(home_id, product_id, quantity, updated_at)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(home_id, product_id)
            DO UPDATE SET quantity = excluded.quantity, updated_at = excluded.updated_at
        """, (home_id, product_id, new_quantity, int(time.time())))
        if add_to_shopping:
            add_shopping_item(conn, product_id, home_id, 1)
        ok = True
    finally:
        commit_or_rollback(conn, ok)
    return jsonify({"ok": True, "quantity": new_quantity})


@app.post("/api/shopping/add")
def shopping_add():
    data = request.get_json(force=True)
    product_id = int(data.get("product_id"))
    home_id = data.get("home_id")
    if home_id in (None, "", "null"):
        return jsonify({"error": "Wybierz dom dla pozycji zakupowej."}), 400
    conn = connect()
    ok = False
    try:
        add_shopping_item(conn, product_id, int(home_id), 1)
        ok = True
    finally:
        commit_or_rollback(conn, ok)
    return jsonify({"ok": True})


@app.post("/api/shopping/<int:item_id>/change")
def shopping_change(item_id: int):
    data = request.get_json(force=True)
    delta = int(data.get("delta"))
    conn = connect()
    ok = False
    try:
        row = fetch_one(conn, "SELECT wanted_quantity FROM shopping_list WHERE id = ?", (item_id,))
        if not row:
            return jsonify({"error": "Nie znaleziono pozycji."}), 404
        qty = row["wanted_quantity"] + delta
        if qty <= 0:
            run(conn, "DELETE FROM shopping_list WHERE id = ?", (item_id,))
        else:
            run(conn, "UPDATE shopping_list SET wanted_quantity = ? WHERE id = ?", (qty, item_id))
        ok = True
    finally:
        commit_or_rollback(conn, ok)
    return jsonify({"ok": True})


@app.post("/api/shopping/<int:item_id>/toggle")
def shopping_toggle(item_id: int):
    conn = connect()
    ok = False
    try:
        row = fetch_one(conn, "SELECT checked FROM shopping_list WHERE id = ?", (item_id,))
        if not row:
            return jsonify({"ok": False, "error": "Nie znaleziono pozycji na liście zakupów."}), 404
        new_checked = 0 if int(row.get("checked") or 0) else 1
        run(conn, "UPDATE shopping_list SET checked = ? WHERE id = ?", (new_checked, item_id))
        ok = True
    finally:
        commit_or_rollback(conn, ok)
    return jsonify({"ok": True})


@app.post("/api/shopping/<int:item_id>/delete")
def shopping_delete(item_id: int):
    conn = connect()
    ok = False
    try:
        run(conn, "DELETE FROM shopping_list WHERE id = ?", (item_id,))
        ok = True
    finally:
        commit_or_rollback(conn, ok)
    return jsonify({"ok": True})


@app.post("/api/shopping/clear_checked")
def shopping_clear_checked():
    conn = connect()
    ok = False
    try:
        run(conn, "DELETE FROM shopping_list WHERE checked = 1")
        ok = True
    finally:
        commit_or_rollback(conn, ok)
    return jsonify({"ok": True})


@app.post("/api/notes")
def notes_add():
    data = request.get_json(silent=True) or {}
    body = (data.get("body") or "").strip()
    if not body:
        return jsonify({"error": "Wpisz treść notatki."}), 400
    conn = connect()
    ok = False
    try:
        run(conn, "INSERT INTO notes(body, done, created_at) VALUES(?, 0, ?)", (body, int(time.time())))
        ok = True
    finally:
        commit_or_rollback(conn, ok)
    return jsonify({"ok": True})


@app.post("/api/notes/<int:note_id>/toggle")
def notes_toggle(note_id: int):
    conn = connect()
    ok = False
    try:
        run(conn, "UPDATE notes SET done = 1 - done WHERE id = ?", (note_id,))
        ok = True
    finally:
        commit_or_rollback(conn, ok)
    return jsonify({"ok": True})


@app.post("/api/notes/<int:note_id>/delete")
def notes_delete(note_id: int):
    conn = connect()
    ok = False
    try:
        run(conn, "DELETE FROM notes WHERE id = ?", (note_id,))
        ok = True
    finally:
        commit_or_rollback(conn, ok)
    return jsonify({"ok": True})


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
