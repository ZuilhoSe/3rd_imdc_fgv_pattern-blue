#!/usr/bin/env bash
# Mede o tempo de 1 época do v3 no servidor, sem e com workers, num corte só.
# Usa sementes descartáveis (_s901, _s902) e apaga os checkpoints e logs delas no fim.
# Uso, a partir da raiz do repositório:  bash hpc/bench.sh > src/outputs/hpc_bench.log 2>&1
set -u
export MAX_EPOCHS=1 PATIENCE=1 FULL_EPOCHS=1 PYTHONIOENCODING=utf-8 CUDA_VISIBLE_DEVICES=${GPU:-0}
PY=${PY:-$(pwd)/.venv/bin/python}
cd src || exit 1
nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv
nproc
for cfg in "0 cut2015_s901" "8 cut2015_s902"; do
  set -- $cfg
  echo "=== NUM_WORKERS=$1 tag=$2"
  NUM_WORKERS=$1 "$PY" -u train_v3.py "$2" 2>&1 | grep -E "amostras|etapa"
  rm -rf "models/checkpoints/v3/$2" "models/logs/v3/$2" "models/logs/v3/$2_full"
done
