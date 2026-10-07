#!/usr/bin/env bash
# Quickstart script for CardioVision AI local full-stack development

set -e

echo "============================================="
echo "Starting CardioVision AI Full-Stack Platform"
echo "============================================="

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

echo "Checking Python dependencies..."
python3 -c "import fastapi, uvicorn, sklearn, xgboost, lightgbm, catboost, shap" || {
    echo "Installing missing backend dependencies..."
    pip install -r backend/requirements.txt
}

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting Backend FastAPI on http://localhost:8000..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

echo "Starting Frontend Vite on http://localhost:5173..."
cd "$ROOT_DIR/frontend"
npm run dev -- --host &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT

echo "CardioVision AI is live!"
echo "Backend: http://localhost:8000 (Swagger docs: http://localhost:8000/docs)"
echo "Frontend: http://localhost:5173"

wait
