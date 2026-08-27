#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OOTD_DIR="${OOTDIFFUSION_PATH:-${PROJECT_ROOT}/vendor/OOTDiffusion}"
VENV_DIR="${OOTDIFFUSION_VENV:-${PROJECT_ROOT}/.venv-ootd}"
PYTHON_BIN="${PYTHON_BIN:-python3.11}"

command -v git >/dev/null || { echo "git is required" >&2; exit 1; }
command -v "${PYTHON_BIN}" >/dev/null || { echo "${PYTHON_BIN} is required" >&2; exit 1; }

if [[ ! -d "${OOTD_DIR}/.git" ]]; then
  mkdir -p "$(dirname "${OOTD_DIR}")"
  git clone --depth 1 https://github.com/levihsu/OOTDiffusion.git "${OOTD_DIR}"
fi

"${PYTHON_BIN}" -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/python" -m pip install --upgrade pip setuptools wheel
"${VENV_DIR}/bin/pip" install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
"${VENV_DIR}/bin/pip" install -r "${OOTD_DIR}/requirements.txt"
"${VENV_DIR}/bin/pip" install "huggingface_hub[cli]"
HF_CLI="${VENV_DIR}/bin/hf"
if [[ ! -x "${HF_CLI}" ]]; then
  HF_CLI="${VENV_DIR}/bin/huggingface-cli"
fi
"${HF_CLI}" download levihsu/OOTDiffusion --local-dir "${OOTD_DIR}"
"${HF_CLI}" download openai/clip-vit-large-patch14 --local-dir "${OOTD_DIR}/checkpoints/clip-vit-large-patch14"
"${VENV_DIR}/bin/pip" install -e "${PROJECT_ROOT}"

echo "OOTDiffusion installed at ${OOTD_DIR}"
echo "Run scripts/run_gpu_worker.sh to start the GPU queue worker."
