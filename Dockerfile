# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile — Mini Kanban Board
# DevOps University Project
#
# Build args injected by Jenkins at build time:
#   APP_VERSION  – e.g. "v1.42"       (defaults to "v1.0-local")
#   ENV_NAME     – "production" | "development" | "local"
#
# Example manual build:
#   docker build \
#     --build-arg APP_VERSION=v1.5 \
#     --build-arg ENV_NAME=development \
#     -t kanban-board:5 .
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage: Base image (Alpine = smallest possible footprint) ──────────────────
FROM python:3.11-alpine

LABEL maintainer="devops-project"
LABEL description="Mini Kanban Board CI/CD Demo"

# ── Build-time arguments (passed in by Jenkins via --build-arg) ───────────────
ARG APP_VERSION=v1.0-local
ARG ENV_NAME=local

# ── Expose args as runtime environment variables inside the container ─────────
ENV APP_VERSION=${APP_VERSION} \
    ENV_NAME=${ENV_NAME} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ── Set working directory ─────────────────────────────────────────────────────
WORKDIR /app

# ── Install Python dependencies ───────────────────────────────────────────────
# Copy requirements first so Docker caches this layer.
# The layer only re-builds when requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy application source code ──────────────────────────────────────────────
COPY . .

# ── Expose the application port ───────────────────────────────────────────────
EXPOSE 5000

# ── Health check (Docker will monitor container health) ───────────────────────
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -qO- http://localhost:5000/status || exit 1

# ── Start the application ─────────────────────────────────────────────────────
CMD ["python", "app.py"]
