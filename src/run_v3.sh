#!/usr/bin/env bash
# Pattern Blue v3: treina e infere um corte por vez; um processo por corte devolve toda a memória ao final.
# Uso, a partir de src/:  bash run_v3.sh > outputs/v3_train.log 2>&1
export PYTHONIOENCODING=utf-8
export MAX_EPOCHS=25 PATIENCE=5 FULL_EPOCHS=3 NUM_WORKERS=0
PY=../.venv/Scripts/python.exe
for tag in final test4 test3 test2 test1 cut2021 cut2020 cut2019 cut2018 cut2017 cut2016 cut2015; do
  echo "[$(date +%F' '%T)] inicio $tag"
  $PY -u train_v3.py "$tag" && $PY -u infer_v3.py "$tag" || echo "FALHOU $tag"
  echo "[$(date +%F' '%T)] fim $tag"
done
