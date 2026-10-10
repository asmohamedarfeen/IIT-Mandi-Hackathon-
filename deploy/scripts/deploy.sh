#!/usr/bin/env bash
# ==============================================================================
# CardioVision AI - Automated Production Deployment Script
# Supports: Ubuntu, Debian, CentOS, macOS, and any Docker-enabled server.
# ==============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

echo "========================================================"
echo "   🫀 CardioVision AI Production Deployment Helper"
echo "========================================================"

# 1. Verify Docker is installed and running
if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Error: Docker is not installed."
    echo "Please install Docker from https://docs.docker.com/engine/install/"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "❌ Error: Docker daemon is not running."
    echo "Please start Docker service: sudo systemctl start docker"
    exit 1
fi

# 2. Check for docker compose plugin
COMPOSE_CMD=""
if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
else
    echo "❌ Error: Docker Compose is not installed."
    exit 1
fi

echo "✅ Docker & Compose detected: $($COMPOSE_CMD version --short 2>/dev/null || echo 'ready')"

# 3. Environment configuration
if [[ ! -f "$ROOT_DIR/.env" ]]; then
    if [[ -f "$ROOT_DIR/.env.example" ]]; then
        echo "ℹ️  No .env file found. Copying .env.example to .env..."
        cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
    fi
fi

# 4. Prompt / Select Compose Configuration
COMPOSE_FILE="docker-compose.yml"
if [[ "${1:-}" == "--prod" ]]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    echo "🚀 Using Production Stack: $COMPOSE_FILE"
else
    echo "📦 Using Standard Stack: $COMPOSE_FILE (use --prod for dedicated server stack)"
fi

# 5. Build and deploy containers
echo "🔨 Building and launching containers..."
$COMPOSE_CMD -f "$COMPOSE_FILE" up -d --build

# 6. Wait for health check
echo "⏳ Waiting for services to become healthy..."
MAX_RETRIES=15
COUNT=0
HEALTHY=false

while [[ $COUNT -lt $MAX_RETRIES ]]; do
    if curl -s -f http://127.0.0.1:8000/health >/dev/null 2>&1 || curl -s -f http://127.0.0.1:80/health >/dev/null 2>&1; then
        HEALTHY=true
        break
    fi
    sleep 3
    COUNT=$((COUNT + 1))
    printf "."
done
echo ""

if [[ "$HEALTHY" == "true" ]]; then
    echo "========================================================"
    echo "🎉 SUCCESS: CardioVision AI is live and healthy!"
    echo "========================================================"
    echo "🌐 Web Dashboard:  http://localhost (or your server IP on port 80)"
    echo "📚 API & Swagger:  http://localhost:8000/docs"
    echo "🩺 Health Check:   http://localhost:8000/health"
    echo ""
    echo "Helpful commands:"
    echo "  - View logs:     $COMPOSE_CMD -f $COMPOSE_FILE logs -f"
    echo "  - Restart:       $COMPOSE_CMD -f $COMPOSE_FILE restart"
    echo "  - Stop:          $COMPOSE_CMD -f $COMPOSE_FILE down"
    echo "========================================================"
else
    echo "⚠️  Services started, but healthcheck is still warming up."
    echo "Check container logs with: $COMPOSE_CMD -f $COMPOSE_FILE logs"
fi
