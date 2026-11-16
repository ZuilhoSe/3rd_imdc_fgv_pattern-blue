#!/bin/bash
#SBATCH --job-name=pb-sementes
#SBATCH --time=24:00:00
#SBATCH --gres=gpu:1
#SBATCH --output=slurm-%x-%j.out
# Rodada de sementes do v3 (emenda E1 do protocolo). Submeter da raiz do repositório:
#   PARALLEL=6 NUM_WORKERS=3 LIBERAR=<jobid> sbatch --export=ALL hpc/slurm_sementes.sh
# LIBERAR (opcional): job em hold liberado com scontrol release quando todas as tags terminarem.
# Os treinos paralelos usam o MPS da NVIDIA: sem ele a GPU alterna entre processos e o paralelismo não rende.
# O próximo job já fica na fila (afterany) e retoma o que faltar; é cancelado quando tudo termina.
# Uma tag está pronta quando existe src/outputs/params/v3<sufixo>/params_<tag>_full.parquet.
# Chikungunya (confirmatório B, emenda E6):
#   DOENCA=chik LIST=hpc/tags_chik.txt PARALLEL=6 NUM_WORKERS=3 sbatch --export=ALL hpc/slurm_sementes.sh
set -u
cd "${SLURM_SUBMIT_DIR:-.}"
export DOENCA=${DOENCA:-dengue}
SUFFIX=$([ "$DOENCA" = dengue ] && echo "" || echo "_$DOENCA")
LIST=${LIST:-hpc/tags_sementes_v3.txt}
PEND=hpc/_pendentes${SUFFIX}.txt
pending() { grep -vE '^\s*(#|$)' "$LIST" | while read -r t; do [ -f "src/outputs/params/v3${SUFFIX}/params_${t}_full.parquet" ] || echo "$t"; done; }
pending > "$PEND"
n=$(wc -l < "$PEND")
echo "[$(date +%F' '%T)] job $SLURM_JOB_ID: $n tags pendentes"
[ "$n" -eq 0 ] && exit 0
next=$(sbatch --parsable --export=ALL --dependency=afterany:"$SLURM_JOB_ID" hpc/slurm_sementes.sh)
echo "próximo job $next aguarda $SLURM_JOB_ID"
export CUDA_MPS_PIPE_DIRECTORY=/tmp/mps_pipe_$SLURM_JOB_ID CUDA_MPS_LOG_DIRECTORY=/tmp/mps_log_$SLURM_JOB_ID
mkdir -p "$CUDA_MPS_PIPE_DIRECTORY" "$CUDA_MPS_LOG_DIRECTORY"
nvidia-cuda-mps-control -d && echo "MPS ativo"
trap 'echo quit | nvidia-cuda-mps-control' EXIT
if [ "$DOENCA" = chik ] && [ ! -f data/processed/base_weekly_v3_chik.parquet ]; then
  (cd src && ../.venv/bin/python -u preprocess_chik.py base_v3) || exit 1
fi
PY=$(pwd)/.venv/bin/python bash hpc/run_parallel.sh "$PEND"
if [ "$(pending | wc -l)" -eq 0 ]; then
  echo "tudo pronto; cancelando $next"; scancel "$next"
  [ -n "${LIBERAR:-}" ] && scontrol release "$LIBERAR" && echo "liberado o job $LIBERAR"
fi
