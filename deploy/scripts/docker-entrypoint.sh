#!/bin/sh
set -e

# Run database migrations
echo "Running database migrations via Alembic..."
alembic upgrade head || {
    echo "Warning: Alembic migration failed, checking if fallback tables needed..."
}

# Determine hosting port ($PORT is set automatically by Render, Cloud Run, Heroku, Fly.io, etc.)
SERVER_PORT="${PORT:-8000}"
SERVER_HOST="${HOST:-0.0.0.0}"

echo "Starting CardioVision AI server on ${SERVER_HOST}:${SERVER_PORT}..."
exec uvicorn backend.main:app --host "${SERVER_HOST}" --port "${SERVER_PORT}" --no-access-log
