# Execução no HPC da FGV (Slurm, 1 A100)

Fase 0 do protocolo congelado (`docs/protocolo_congelado_2026-11-15.md`, emenda E1): v3 com 5 sementes nos 10 cortes de desenvolvimento.

Regras do HPC: nada pesado no `hpchead`; treino só via `sbatch`; `--time` até 24 h; sem `--mem` nem `--cpus-per-task`; um job por vez.

1. No `hpchead`: `git clone` do repositório e `git checkout fase0/versionamento`.
2. Dados (fora do git), por `scp`: `data/processed/base_weekly_v3.parquet`, `data/processed/season_targets_v3.parquet` e `data/processed/base_weekly.parquet` (o v3 ainda lê UF e regional dela em `common.season_targets_for_cut`). Conferir com `sha256sum` contra `reports/manifesto_artefatos_2026-11-15.sha256`.
3. Ambiente no `hpchead`: `uv venv --python 3.12 && uv pip install torch==2.6.0 --torch-backend=cu124 && uv pip install -r hpc/requirements_v3.txt`.
4. Medir: `sbatch hpc/slurm_bench.sh`. Escolher `PARALLEL` e `NUM_WORKERS` pelos núcleos, pela memória e pelo tempo por época.
5. Rodar: `PARALLEL=6 NUM_WORKERS=4 sbatch --export=ALL hpc/slurm_sementes.sh`. Se passar de 24 h, o job seguinte retoma sozinho.
6. Acompanhar: `squeue --me`; `cat src/outputs/hpc_logs/_resumo.log`.
7. Trazer de volta: `src/models/checkpoints/v3/*_s*`, `src/models/logs/v3/*_s*`, `src/outputs/params/v3/*_s*` e `src/outputs/hpc_logs/`. O tráfego de saída é cobrado da FGV: só o necessário.

`run_parallel.sh` e `bench.sh` também servem numa máquina sem Slurm.
