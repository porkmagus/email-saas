# Backend Dockerfile — FastAPI on Python 3.13
# Multi-stage build for small image and fast rebuilds

# Build stage: install dependencies
FROM python:3.13.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN pip install --no-cache-dir uv==0.6.14

# Copy source code needed for editable install
COPY api/ ./api/
COPY migrations/ ./migrations/
COPY scripts/ ./scripts/
COPY tests/ ./tests/
COPY pyproject.toml ./

# Install dependencies into a virtual environment
RUN uv venv /opt/venv && \
    uv pip install --python /opt/venv/bin/python -e ".[dev]"

# Runtime stage
FROM python:3.13.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install runtime libpq
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual env from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY api/ ./api/
COPY migrations/ ./migrations/
COPY scripts/ ./scripts/
COPY tests/ ./tests/
COPY pyproject.toml ./

# Non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose and run with uvicorn workers
# Use 2*CPU+1 workers in production; adjust via WORKERS env var
ENV WORKERS=4
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"

CMD ["sh", "-c", "uvicorn api.main:app --host ${HOST} --port ${PORT} --workers ${WORKERS} --proxy-headers --forwarded-allow-ips='*'"]
