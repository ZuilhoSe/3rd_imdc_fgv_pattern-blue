#!/usr/bin/env bash
# Treina e infere várias tags do v3 em paralelo na mesma máquina.
# Uso, a partir da raiz do repositório no servidor:
#   bash hpc/run_parallel.sh hpc/tags_sementes_v3.txt            # padrão: 8 em paralelo, 4 workers cada
#   PARALLEL=12 NUM_WORKERS=6 GPU=0 bash hpc/run_parallel.sh lista.txt
# Retoma sozinho: train_v3.py pula a tag se full.ckpt já existe; infer_v3.py regrava os parâmetros.
# Logs: src/outputs/hpc_logs/<tag>.log e um resumo em src/outputs/hpc_logs/_resumo.log
set -u
LIST=${1:?lista de tags}
PARALLEL=${PARALLEL:-8}
export NUM_WORKERS=${NUM_WORKERS:-4}
export CUDA_VISIBLE_DEVICES=${GPU:-0}
export MAX_EPOCHS=25 PATIENCE=5 FULL_EPOCHS=3          # iguais a src/run_v3.sh
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
PY=${PY:-$(pwd)/.venv/bin/python}
LISTABS=$(readlink -f "$LIST")
cd src || exit 1
mkdir -p outputs/hpc_logs
run_one() {
  tag=$1
  echo "[$(date +%F' '%T)] inicio $tag" >> outputs/hpc_logs/_resumo.log
  if "$PY" -u train_v3.py "$tag" && "$PY" -u infer_v3.py "$tag"; then st=ok; else st=FALHOU; fi > "outputs/hpc_logs/$tag.log" 2>&1
  echo "[$(date +%F' '%T)] fim $tag $st" >> outputs/hpc_logs/_resumo.log
}
export -f run_one; export PY
grep -vE '^\s*(#|$)' "$LISTABS" | xargs -P "$PARALLEL" -I{} bash -c 'run_one "$@"' _ {}
echo "[$(date +%F' '%T)] lista concluída" >> outputs/hpc_logs/_resumo.log
