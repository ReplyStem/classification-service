# Classification Microservice Dockerfile
# Multi-stage build for smaller final image

# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: Builder - Install dependencies
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-alpine AS builder

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: Runtime - Final slim image
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-alpine AS runtime

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN addgroup -g 1001 -S appuser && \
    adduser -S -D -H -u 1001 -h /app -s /sbin/nologin -G appuser -g appuser appuser && \
    mkdir -p /app/logs && \
    mkdir -p /app/.cache/huggingface && \
    chown -R appuser:appuser /app

# Copy application code (exclude unnecessary files)
COPY --chown=appuser:appuser api/ ./api/
COPY --chown=appuser:appuser auth/ ./auth/
COPY --chown=appuser:appuser classifiers/ ./classifiers/
COPY --chown=appuser:appuser config/ ./config/
COPY --chown=appuser:appuser message_queue/ ./message_queue/
COPY --chown=appuser:appuser models/ ./models/
COPY --chown=appuser:appuser utils/ ./utils/
COPY --chown=appuser:appuser workers/ ./workers/
COPY --chown=appuser:appuser main.py .

# Switch to non-root user
USER appuser

# Environment variables (can be overridden at runtime)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO \
    LOG_FILE=logs/classification_service.log \
    API_HOST=0.0.0.0 \
    API_PORT=8000

# Expose health check port
EXPOSE 8000

# Health check using httpx (already in requirements)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import httpx; r = httpx.get('http://localhost:8000/health'); exit(0 if r.status_code == 200 else 1)"

# Run the service
CMD ["python", "main.py"]
