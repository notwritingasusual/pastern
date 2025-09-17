from flask import Flask, render_template, request, redirect, url_for, jsonify, g
import sqlite3
import os

app = Flask(__name__)
DB_FILE = "database.db"

# -----------------------------
# Database helpers
# -----------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_FILE, timeout=10, check_same_thread=False)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            image_path TEXT,
            keywords TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.commit()

# -----------------------------
# Website routes
# -----------------------------
@app.route("/", methods=["GET"])
def index():
    db = get_db()
    entries = db.execute("SELECT * FROM entries ORDER BY created_at DESC").fetchall()
    return render_template("index.html", entries=entries)

@app.route("/", methods=["POST"])
def add_entry():
    title = request.form.get("title")
    content = request.form.get("content")
    keywords = request.form.get("keywords", "")
    image = request.files.get("image")

    image_path = None
    if image and image.filename:
        os.makedirs("static/uploads", exist_ok=True)
        image_path = os.path.join("static/uploads", image.filename)
        image.save(image_path)

    db = get_db()
    db.execute(
        "INSERT INTO entries (title, content, keywords, image_path) VALUES (?, ?, ?, ?)",
        (title, content, keywords, image_path)
    )
    db.commit()
    return redirect(url_for("index"))

# -----------------------------
# API routes (CRUD)
# -----------------------------
@app.route("/api/entries", methods=["GET"])
def api_get_entries():
    db = get_db()
    rows = db.execute("SELECT * FROM entries ORDER BY created_at DESC").fetchall()
    return jsonify([dict(row) for row in rows])

@app.route("/api/entries", methods=["POST"])
def api_add_entry():
    data = request.json
    title = data.get("title")
    content = data.get("content")
    keywords = data.get("keywords", "")
    image_path = data.get("image_path", None)

    db = get_db()
    db.execute(
        "INSERT INTO entries (title, content, keywords, image_path) VALUES (?, ?, ?, ?)",
        (title, content, keywords, image_path)
    )
    db.commit()
    return jsonify({"status": "ok", "message": "Entry created"}), 201

@app.route("/api/entries/<int:id>", methods=["DELETE"])
def api_delete_entry(id):
    db = get_db()
    db.execute("DELETE FROM entries WHERE id = ?", (id,))
    db.commit()
    return jsonify({"status": "ok", "message": f"Entry {id} deleted"}), 200

@app.route("/api/entries/<int:id>", methods=["PUT"])
def api_update_entry(id):
    data = request.json
    title = data.get("title")
    content = data.get("content")
    keywords = data.get("keywords", "")
    image_path = data.get("image_path", None)

    db = get_db()
    db.execute(
        "UPDATE entries SET title = ?, content = ?, keywords = ?, image_path = ? WHERE id = ?",
        (title, content, keywords, image_path, id)
    )
    db.commit()
    return jsonify({"status": "ok", "message": f"Entry {id} updated"}), 200

# -----------------------------
# Run the app
# -----------------------------
if __name__ == "__main__":
    with app.app_context():
        init_db()  # safely initialize DB inside app context
    app.run(debug=True)
