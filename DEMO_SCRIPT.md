# Live Evaluation Demo Script
## Mini Kanban Board — DevOps CI/CD Project

> **Total demo time:** ~8–10 minutes  
> **Have open before you begin:** Jenkins dashboard, two browser tabs (ports 5000 and 5001), your code editor, and a terminal.

---

## Pre-Demo Checklist (Do this 10 minutes before)

- [ ] `main` branch is deployed → `http://localhost:5000` loads the board
- [ ] Jenkins is running and the Multibranch Pipeline job is configured
- [ ] GitHub webhooks are verified (push → triggers Jenkins automatically)
- [ ] Your editor has `templates/index.html` and `test_app.py` open in tabs
- [ ] You have a clean `feature-dark-mode` branch ready to create

---

## Demo Scene 1 — Show the Live Production App (2 min)

**What you say:**  
*"This is our production Kanban board, running live inside a Docker container on port 5000. It was deployed automatically by our Jenkins pipeline after a merge to the `main` branch."*

**What you do:**
- Open `http://localhost:5000` — show the board with its three columns
- Point to the **footer**: version, environment (`production`), status (`healthy`)
- Point to the **green `production` badge** in the header
- Add a task live: type "Demonstrate CI/CD to evaluator" → Enter
- Move it from To-Do → In Progress → Done using the arrow buttons

**Key talking point:**  
*"Notice the footer shows `environment: production` and a version number. These are injected by Jenkins at build time using Docker `--build-arg` flags — the application has no hardcoded config."*

---

## Demo Scene 2 — Feature Branch → Dev Deployment (4 min)

**What you say:**  
*"Now I'll simulate a developer working on a new feature — a dark mode UI redesign — and show how it goes from a feature branch to our isolated development environment without ever touching production."*

**What you do (in terminal):**

```bash
# 1. Create the feature branch
git checkout -b feature-dark-mode

# 2. Open templates/index.html and change ONE line:
#    <html lang="en" data-theme="light">
#                               ↓ change to ↓
#    <html lang="en" data-theme="dark">

# 3. Commit and push to dev
git add templates/index.html
git commit -m "feat: add dark mode UI theme"
git checkout dev
git merge feature-dark-mode
git push origin dev
```

**Switch to Jenkins dashboard:**
- Watch the `dev` branch pipeline trigger automatically (within ~30 seconds of the push)
- Walk through each stage as it runs: Checkout → Install → Quality Gate → Build → Deploy
- Point out Stage 3 turning **green** — *"All 8 tests passed. The quality gate is open."*
- Point out Stage 5 log: *"Deploying to DEVELOPMENT (port 5001)"*

**Switch to browser:**
- Open `http://localhost:5001` — **the dark UI appears**
- Open `http://localhost:5000` beside it — **still the original light theme**

**Key talking point:**  
*"Both environments are running simultaneously inside separate Docker containers. The dev container was replaced with the new dark-mode build. Production was never touched. This is exactly how real teams ship features safely."*

---

## Demo Scene 3 — Intentional Test Failure / Quality Gate (3 min)

**What you say:**  
*"Now I'll show what happens when a developer introduces a bug. Our pipeline acts as a safety net — bad code cannot reach a running environment."*

**What you do (in editor — `test_app.py`):**

Find the `test_new_task_lands_in_todo_column` function.  
Change line:
```python
assert data["column"] == "todo"
```
to:
```python
assert data["column"] == "done"   # ← the intentional bug
```

**In terminal:**
```bash
git add test_app.py
git commit -m "bug: incorrect column assertion (demo)"
git push origin dev
```

**Switch to Jenkins — watch the pipeline:**

| Stage | Status |
|-------|--------|
| Stage 1 — Checkout | ✅ |
| Stage 2 — Install | ✅ |
| Stage 3 — Quality Gate | 🚨 **FAILED** |
| Stage 4 — Build | ⛔ Skipped |
| Stage 5 — Deploy | ⛔ Skipped |

- Click into **Stage 3 logs** and show the error:
  ```
  AssertionError: assert 'todo' == 'done'
  FAILED test_app.py::test_new_task_lands_in_todo_column
  1 failed, 7 passed
  ```
- Show `http://localhost:5001` — **the old container is still running unchanged**

**Key talking point:**  
*"The pipeline halted at the Quality Gate. Stage 4 and Stage 5 were never reached. The Docker build never ran. The container was never replaced. This is the core value of CI/CD — automated testing as a mandatory checkpoint, not an optional step."*

**Recovery (optional, if time allows):**
```bash
# Revert the bug and push again
# Change 'done' back to 'todo' in test_app.py
git add test_app.py
git commit -m "fix: restore correct column assertion"
git push origin dev
```
Watch Jenkins go green and the deployment succeed.

---

## Key Concepts to Mention (if asked by evaluator)

| Question | Answer |
|----------|--------|
| *"Why Docker?"* | Eliminates "works on my machine" — the app runs identically everywhere. Alpine base image keeps it under 100MB. |
| *"Why two ports?"* | Simulates real environment isolation. Dev is where you validate; prod is what users see. |
| *"What triggers Jenkins?"* | GitHub Webhooks. Every `git push` sends an HTTP POST to Jenkins which starts the pipeline automatically. |
| *"What is `--build-arg`?"* | Docker build arguments that pass values from Jenkins into the image at build time, becoming `ENV` variables at runtime. |
| *"Why virtualenv in Jenkins?"* | Isolates Python packages per build. Prevents version conflicts on the shared Jenkins agent. |
| *"What is fail-fast?"* | If Stage 3 fails, Jenkins immediately stops. No wasted time building or deploying broken code. |
| *"How do you promote to prod?"* | Merge `dev` → `main`. Jenkins triggers the same pipeline but routes Stage 5 to port 5000 with `ENV_NAME=production`. |

---

## File Structure Reference

```
kanban-board/
├── app.py              ← Flask backend (API + /status endpoint)
├── requirements.txt    ← Python dependencies
├── test_app.py         ← Pytest test suite (includes demo bug test)
├── Dockerfile          ← Container definition (accepts --build-arg)
├── Jenkinsfile         ← 5-stage declarative CI/CD pipeline
├── .gitignore
└── templates/
    └── index.html      ← Single-page Kanban UI (dark mode toggle here)
```
