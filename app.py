import os
import uuid
import sqlite3
from flask import Flask, jsonify, request, render_template, g

app = Flask(__name__)

APP_VERSION = os.environ.get("APP_VERSION", "v1.0-local")
ENV_NAME    = os.environ.get("ENV_NAME",    "local")

VALID_COLUMNS = {"todo", "inprogress", "done"}
DATABASE      = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kanban.db")


def get_db():
    """Open a database connection scoped to the current request."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    """Close the database connection when the request ends."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create the tasks table if it does not exist, and seed demo data."""
    db = sqlite3.connect(DATABASE)
    db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id     TEXT PRIMARY KEY,
            title  TEXT NOT NULL,
            column_name TEXT NOT NULL DEFAULT 'todo'
        )
    """)
    # Seed demo data only if the table is empty
    count = db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    if count == 0:
        demo = [
            (str(uuid.uuid4()), "Configure Jenkins Pipeline",  "done"),
            (str(uuid.uuid4()), "Write Dockerfile",            "done"),
            (str(uuid.uuid4()), "Set up GitHub Webhooks",      "inprogress"),
            (str(uuid.uuid4()), "Deploy to Production",        "todo"),
            (str(uuid.uuid4()), "Write automated test suite",  "todo"),
        ]
        db.executemany("INSERT INTO tasks (id, title, column_name) VALUES (?, ?, ?)", demo)
    db.commit()
    db.close()


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/status")
def status():
    """DevOps status endpoint — version, environment, and health check."""
    return jsonify({
        "version":     APP_VERSION,
        "environment": ENV_NAME,
        "status":      "healthy",
    })


@app.route("/tasks", methods=["GET"])
def get_tasks():
    """Return all tasks as a JSON array."""
    db   = get_db()
    rows = db.execute("SELECT id, title, column_name FROM tasks").fetchall()
    return jsonify([{"id": r["id"], "title": r["title"], "column": r["column_name"]} for r in rows])


@app.route("/tasks", methods=["POST"])
def add_task():
    """
    Add a new task to the To-Do column.
    Body: { "title": "<string>" }
    Returns: the created task object (HTTP 201).
    """
    body  = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    if not title:
        return jsonify({"error": "Title is required"}), 400

    task_id = str(uuid.uuid4())
    db = get_db()
    db.execute("INSERT INTO tasks (id, title, column_name) VALUES (?, ?, ?)",
               (task_id, title, "todo"))
    db.commit()
    return jsonify({"id": task_id, "title": title, "column": "todo"}), 201


@app.route("/tasks/<task_id>", methods=["PUT"])
def move_task(task_id):
    """
    Move a task to a different column.
    Body: { "column": "todo" | "inprogress" | "done" }
    """
    body   = request.get_json(silent=True) or {}
    column = body.get("column", "")

    if column not in VALID_COLUMNS:
        return jsonify({"error": f"Invalid column '{column}'"}), 400

    db     = get_db()
    cursor = db.execute("UPDATE tasks SET column_name = ? WHERE id = ?", (column, task_id))
    db.commit()

    if cursor.rowcount == 0:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({"id": task_id, "column": column})


@app.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    """Remove a task by ID."""
    db     = get_db()
    cursor = db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()

    if cursor.rowcount == 0:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"message": "Deleted"}), 200


# ── Entry point ───────────────────────────────────────────────────────────────

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
