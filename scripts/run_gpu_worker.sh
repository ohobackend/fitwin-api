#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export OOTDIFFUSION_PATH="${OOTDIFFUSION_PATH:-${PROJECT_ROOT}/vendor/OOTDiffusion}"
VENV_DIR="${OOTDIFFUSION_VENV:-${PROJECT_ROOT}/.venv-ootd}"
cd "${PROJECT_ROOT}"
exec "${VENV_DIR}/bin/celery" -A app.worker.celery_app worker -Q gpu --concurrency=1 --loglevel=info
