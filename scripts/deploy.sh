#!/usr/bin/env bash
set -euo pipefail

DEPLOY_DIR="${DEPLOY_DIR:-/opt/evalforge}"
IMAGE="ghcr.io/fatec-boys/evalforge:latest"

echo "[deploy] pulling latest image..."
docker pull "$IMAGE"

echo "[deploy] applying migrations..."
docker run --rm \
  --env-file "$DEPLOY_DIR/.env" \
  --network host \
  "$IMAGE" \
  sh -c "cd /app && alembic upgrade head"

echo "[deploy] restarting services..."
cd "$DEPLOY_DIR"
docker compose -f docker-compose.prod.yml up -d --remove-orphans

echo "[deploy] removing dangling images..."
docker image prune -f

echo "[deploy] done."
