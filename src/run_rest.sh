#!/usr/bin/env bash
# Encadeia (sequencialmente — a RAM não comporta processos em paralelo):
#   inferência + submissão da previsão final -> treino/inferência das validações
#   -> calibração de rho -> reconstrução de todas as submissões -> avaliação WIS.
set -e
cd "$(dirname "$0")"
PY=../.venv/Scripts/python.exe
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1

echo "[$(date +%T)] inferência final";   $PY run_inference.py final
echo "[$(date +%T)] submissão final";    $PY build_submissions.py final
echo "[$(date +%T)] treino validações";  MAX_EPOCHS=8 PATIENCE=3 $PY train.py test1 test2 test3 test4
echo "[$(date +%T)] inferência validações"; $PY run_inference.py test1 test2 test3 test4
echo "[$(date +%T)] calibra rho";        $PY evaluate.py tune
echo "[$(date +%T)] submissões (todas)"; $PY build_submissions.py
echo "[$(date +%T)] avaliação";          $PY evaluate.py outputs/submissions v2 | tee outputs/eval_v2.txt
echo "[$(date +%T)] FIM"
