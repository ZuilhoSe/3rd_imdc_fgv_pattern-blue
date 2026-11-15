#!/bin/bash
#SBATCH --job-name=pb-bench
#SBATCH --time=02:00:00
#SBATCH --gres=gpu:1
#SBATCH --output=slurm-%x-%j.out
# Medição de 1 época do v3 no nó de GPU (hpcgpu). Submeter da raiz do repositório:
#   sbatch hpc/slurm_bench.sh
set -u
cd "${SLURM_SUBMIT_DIR:-.}"
echo "nó: $(hostname) | núcleos: $(nproc)"; free -g | head -2
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
export MAX_EPOCHS=1 PATIENCE=1 FULL_EPOCHS=1 PYTHONIOENCODING=utf-8
PY=$(pwd)/.venv/bin/python
cd src
for cfg in "0 cut2015_s901" "8 cut2015_s902"; do
  set -- $cfg
  echo "=== NUM_WORKERS=$1 tag=$2"
  NUM_WORKERS=$1 /usr/bin/time -v "$PY" -u train_v3.py "$2" 2>&1 | grep -E "amostras|etapa|Maximum resident|Elapsed|Error|error" 
  rm -rf "models/checkpoints/v3/$2" "models/logs/v3/$2" "models/logs/v3/$2_full"
done
