# Apresentação IMDC 2026 (5 min)

`python presentation/analysis.py` (da raiz do repo) gera as figuras em `figures/` e as
tabelas em `results/` usadas nos slides.

- **Avaliação:** total da temporada por município e por UF nas validações completas
  (test1→2022-23, test2→2023-24, test3→2024-25; 2025-26 ainda incompleta nos dados).
  A série semanal observada (`base_weekly.parquet`) não está versionada, por isso a
  avaliação usa `season_targets.parquet`. Fator de erro = exp(|log((prev+1)/(obs+1))|).
- **Estados:** total por Monte Carlo com a mesma cópula das submissões (rho de
  `src/outputs/state_rho.json`), ES excluído.
- **Ranking de cidades:** ≥ 100 mil hab. e ≥ 200 casos/temporada, sem ES.
- **Baselines:** repetir a temporada anterior; mediana das 3 últimas.
- **Dados externos (`data/`):** malha das UFs (click_that_hood), malha municipal
  simplificada (tbrugz/geodata-br) e população municipal 2021 (wcota/covid19br).

Os números de `reports/` são do modelo anterior (julho) e não refletem o pipeline atual.
