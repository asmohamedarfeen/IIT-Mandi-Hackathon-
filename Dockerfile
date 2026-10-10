# ==============================================================================
# CardioVision AI - Unified All-in-One Production Dockerfile
# Optimized for single-container cloud hosting: Render, Railway, Fly.io, Cloud Run
# ==============================================================================

# Stage 1: Build Frontend SPA
FROM node:24-alpine AS frontend-builder
WORKDIR /build

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# Stage 2: Production Python Backend Runtime
FROM python:3.11-slim AS runtime
WORKDIR /app

# Install system dependencies (curl for healthcheck, libgomp1 for LightGBM/XGBoost OpenMP)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install pinned Python dependencies
COPY backend/requirements.txt backend/requirements.lock.txt /app/
RUN pip install --no-cache-dir -r requirements.lock.txt && pip check

# Copy backend application source and model serving weights
COPY backend /app/backend
COPY artifacts/cardiovision_ensemble.joblib artifacts/heart_model_anatomy.json artifacts/benchmark_summary.json /app/artifacts/
COPY db/migrations /app/db/migrations
COPY alembic.ini /app/alembic.ini
RUN mkdir -p /app/data

# Copy built frontend assets into the static serving location
COPY --from=frontend-builder /build/dist /app/frontend/dist

# Copy entrypoint script
COPY deploy/scripts/docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Environment variables
ENV PYTHONPATH=/app
ENV PORT=8000
ENV HOST=0.0.0.0
ENV DATABASE_URL=sqlite:////app/data/cardiovision.db
ENV ARTIFACTS_DIR=/app/artifacts
ENV AUTO_CREATE_TABLES=false
ENV SERVE_FRONTEND=true
ENV PYTHONDONTWRITEBYTECODE=1
ENV MPLCONFIGDIR=/tmp/matplotlib

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl --fail --silent http://127.0.0.1:${PORT:-8000}/health || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
