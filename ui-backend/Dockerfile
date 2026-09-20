# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update \
  && apt-get install -y --no-install-recommends curl ffmpeg \
  && rm -rf /var/lib/apt/lists/*

RUN groupadd --system --gid 1001 appgroup \
 && useradd --system --uid 1001 --gid appgroup appuser

COPY --from=builder /install /usr/local
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./alembic.ini

# Entrypoint script handles migration + server start
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

USER appuser
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
  CMD curl -sf http://localhost:8000/api/v1/health || exit 1

ENTRYPOINT ["./entrypoint.sh"]
