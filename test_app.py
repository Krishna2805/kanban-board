"""
test_app.py — Automated Test Suite for Mini Kanban Board
=========================================================
Run locally:  pytest test_app.py -v
Run in CI:    pytest test_app.py -v --tb=short

Contains:
  • 7 normal passing tests
  • 1 clearly labelled "Demo Bug" test for live pipeline failure demo
"""

import os
import tempfile
import pytest
import app as app_module
from app import app



@pytest.fixture
def client(tmp_path):
    """Provide a configured Flask test client with an isolated temp database."""
    db_path = str(tmp_path / "test_kanban.db")
    app_module.DATABASE = db_path
    app_module.init_db()

    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def reset_task_store(tmp_path):
    """
    Automatically reset the database before and after every test.
    Uses a temporary database file to guarantee full test isolation.
    """
    db_path = str(tmp_path / "test_kanban.db")
    app_module.DATABASE = db_path

    # Reinitialise with a clean database for each test
    import sqlite3
    db = sqlite3.connect(db_path)
    db.execute("DROP TABLE IF EXISTS tasks")
    db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id     TEXT PRIMARY KEY,
            title  TEXT NOT NULL,
            column_name TEXT NOT NULL DEFAULT 'todo'
        )
    """)
    db.commit()
    db.close()

    yield

    # Cleanup after test
    if os.path.exists(db_path):
        os.remove(db_path)


# ── /status Endpoint Tests ────────────────────────────────────────────────────

def test_status_endpoint_returns_200(client):
    """/status must be reachable and return HTTP 200."""
    response = client.get("/status")
    assert response.status_code == 200


def test_status_endpoint_returns_json(client):
    """/status must return valid JSON."""
    response = client.get("/status")
    data = response.get_json()
    assert data is not None


def test_status_has_required_keys(client):
    """The /status payload must expose 'version', 'environment', and 'status'."""
    data = client.get("/status").get_json()
    assert "version"     in data, "Missing key: 'version'"
    assert "environment" in data, "Missing key: 'environment'"
    assert "status"      in data, "Missing key: 'status'"


def test_status_reports_healthy(client):
    """The 'status' field must always report the string 'healthy'."""
    data = client.get("/status").get_json()
    assert data["status"] == "healthy"


# ── /tasks Endpoint Tests ─────────────────────────────────────────────────────

def test_get_tasks_returns_list(client):
    """GET /tasks must return a JSON array (even when empty)."""
    response = client.get("/tasks")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_add_task_returns_201(client):
    """POST /tasks with a valid title must return HTTP 201 Created."""
    response = client.post("/tasks", json={"title": "Deploy to Kubernetes"})
    assert response.status_code == 201


def test_add_task_stores_correct_title(client):
    """The created task must store exactly the title that was submitted."""
    title    = "Write Jenkinsfile"
    response = client.post("/tasks", json={"title": title})
    data     = response.get_json()
    assert data["title"] == title


def test_add_task_without_title_returns_400(client):
    """Submitting an empty title must be rejected with HTTP 400 Bad Request."""
    response = client.post("/tasks", json={"title": ""})
    assert response.status_code == 400



#  WHAT THIS TEST VALIDATES:
#    Every new task must be placed in the 'todo' column by default.
#    This is a fundamental business rule of the Kanban workflow.
#
#    Step 1 ► Open this file and find the assert line below.
#             Change  'todo'  →  'done'   (an intentionally wrong value)
#
#    Step 2 ► Save the file, then commit and push to the dev branch:
#
#    WHAT JENKINS WILL DO:
#      Stage 1 (Checkout)     — ✅  passes
#      Stage 2 (Install)      — ✅  passes
#      Stage 3 (Quality Gate) — 🚨  FAILS with:
#                                    AssertionError: assert 'todo' == 'done'
#      Stage 4 (Build)        — ⛔  SKIPPED — never reached
#      Stage 5 (Deploy)       — ⛔  SKIPPED — never reached
#
# ─────────────────────────────────────────────────────────────────────────────
def test_new_task_lands_in_todo_column(client):
    """A freshly created task must start in the 'todo' column."""
    response = client.post("/tasks", json={"title": "Demo Bug Task"})
    assert response.status_code == 201
    data = response.get_json()

    assert data["column"] == "todo"
