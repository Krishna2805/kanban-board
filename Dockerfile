
# Build args injected by Jenkins at build time:
#   APP_VERSION  – e.g. "v1.42"       (defaults to "v1.0-local")
#   ENV_NAME     – "production" | "development" | "local"
#
FROM python:3.11-alpine

LABEL maintainer="devops-project"
LABEL description="Mini Kanban Board CI/CD Demo"

ARG APP_VERSION=v1.0-local
ARG ENV_NAME=local

ENV APP_VERSION=${APP_VERSION} \
    ENV_NAME=${ENV_NAME} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ── Install Python dependencies ───────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# ── Health check (Docker will monitor container health) ───────────────────────
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -qO- http://localhost:5000/status || exit 1

CMD ["python", "app.py"]
