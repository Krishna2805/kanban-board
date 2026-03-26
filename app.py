"""
Mini Kanban Board — Backend
DevOps University Project

Environment variables (injected by Docker/Jenkins at runtime):
  APP_VERSION  – e.g. "v1.42"         (default: "v1.0-local")
  ENV_NAME     – "production" | "development" | "local"
"""

import os
import uuid
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

# ── In-memory task store (seeded with demo data) ─────────────────────────────
tasks = [
    {"id": str(uuid.uuid4()), "title": "Pipeline is fully automated 🚀", "column": "done"},
    {"id": str(uuid.uuid4()), "title": "Configure Jenkins Pipeline",  "column": "done"},
    {"id": str(uuid.uuid4()), "title": "Write Dockerfile",            "column": "done"},
    {"id": str(uuid.uuid4()), "title": "Set up GitHub Webhooks",      "column": "inprogress"},
    {"id": str(uuid.uuid4()), "title": "Deploy to Production",        "column": "todo"},
    {"id": str(uuid.uuid4()), "title": "Write automated test suite",  "column": "todo"},
]

# ── Runtime config (set via Docker -e flags) ──────────────────────────────────
APP_VERSION = os.environ.get("APP_VERSION", "v1.0-local")
ENV_NAME    = os.environ.get("ENV_NAME",    "local")

VALID_COLUMNS = {"todo", "inprogress", "done"}


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
    return jsonify(tasks)


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

    task = {
        "id":     str(uuid.uuid4()),
        "title":  title,
        "column": "todo",          # all new tasks start here
    }
    tasks.append(task)
    return jsonify(task), 201


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

    for task in tasks:
        if task["id"] == task_id:
            task["column"] = column
            return jsonify(task)

    return jsonify({"error": "Task not found"}), 404


@app.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    """Remove a task by ID."""
    global tasks
    before = len(tasks)
    tasks  = [t for t in tasks if t["id"] != task_id]
    if len(tasks) == before:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"message": "Deleted"}), 200


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
