# Execução no servidor (multigpu)

Fase 0 do protocolo congelado (`docs/protocolo_congelado_2026-11-15.md`): v3 com 5 sementes nos 10 cortes de desenvolvimento.

1. Código: `git clone` do repositório e `git checkout fase0/versionamento`.
2. Dados (fora do git): `data/processed/base_weekly_v3.parquet` e `data/processed/season_targets_v3.parquet`. Conferir com `sha256sum -c` contra as linhas correspondentes de `reports/manifesto_artefatos_2026-11-15.sha256`.
3. Ambiente: `python3.12 -m venv .venv && .venv/bin/pip install -r hpc/requirements_v3.txt` (torch com a roda CUDA do servidor).
4. Medir: `bash hpc/bench.sh > src/outputs/hpc_bench.log 2>&1`. Escolher `PARALLEL` e `NUM_WORKERS` pelos núcleos livres e pelo tempo por época.
5. Rodar: `nohup bash hpc/run_parallel.sh hpc/tags_sementes_v3.txt > /dev/null 2>&1 &`
6. Trazer de volta: `src/models/checkpoints/v3/*_s*`, `src/models/logs/v3/*_s*`, `src/outputs/params/v3/*_s*` e `src/outputs/hpc_logs/`.
