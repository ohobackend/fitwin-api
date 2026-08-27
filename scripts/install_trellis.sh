#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRELLIS_DIR="${TRELLIS_PATH:-${PROJECT_ROOT}/vendor/TRELLIS}"
VENV_DIR="${TRELLIS_VENV:-${PROJECT_ROOT}/.venv-trellis}"
PYTHON_BIN="${PYTHON_BIN:-python3.11}"
if [[ ! -d "${TRELLIS_DIR}/.git" ]]; then
  mkdir -p "$(dirname "${TRELLIS_DIR}")"
  git clone --recurse-submodules https://github.com/microsoft/TRELLIS.git "${TRELLIS_DIR}"
fi
"${PYTHON_BIN}" -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip setuptools wheel
pip install torch==2.4.0 torchvision==0.19.0 --index-url https://download.pytorch.org/whl/cu118
cd "${TRELLIS_DIR}"
source ./setup.sh --basic --xformers --diffoctreerast --spconv --mipgaussian --kaolin --nvdiffrast
pip install "huggingface_hub[cli]"
HF_CLI="${VENV_DIR}/bin/hf"
[[ -x "${HF_CLI}" ]] || HF_CLI="${VENV_DIR}/bin/huggingface-cli"
"${HF_CLI}" download microsoft/TRELLIS-image-large --local-dir "${TRELLIS_DIR}/checkpoints/TRELLIS-image-large"
pip install -e "${PROJECT_ROOT}"
echo "TRELLIS installed. Run scripts/run_trellis_worker.sh"
