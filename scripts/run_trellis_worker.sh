#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export TRELLIS_PATH="${TRELLIS_PATH:-${PROJECT_ROOT}/vendor/TRELLIS}"
export TRELLIS_MODEL_ID="${TRELLIS_MODEL_ID:-${TRELLIS_PATH}/checkpoints/TRELLIS-image-large}"
export ATTN_BACKEND="${ATTN_BACKEND:-xformers}"
VENV_DIR="${TRELLIS_VENV:-${PROJECT_ROOT}/.venv-trellis}"
cd "${PROJECT_ROOT}"
exec "${VENV_DIR}/bin/celery" -A app.worker.celery_app worker -Q gpu_3d --concurrency=1 --loglevel=info
