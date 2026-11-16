"""
Confirmatório B do protocolo congelado (seção 6, emenda E6): chikungunya como alvo.

Mesmo pré-processamento de dengue, trocando as séries:
  * a série de chikungunya ocupa o lugar da de dengue (casos e incidência);
  * a de dengue ocupa o lugar da covariável de chikungunya (log_casos_chik);
  * o resto (clima, população, estáticas, acessos Afya) não muda.

A série de chikungunya do FTP começa na EW01/2014. As semanas anteriores saem da base (não viram
zero): a temporada 2014 fica incompleta e a primeira temporada completa é a 2015.

Gera, a partir das tabelas de dengue (que ficam intactas):
  data/processed/base_weekly_chik.parquet       <- base_weekly.parquet  (baselines e verdade)
  data/processed/season_targets_chik.parquet    <- ajustes do episcanner de chikungunya (B3)
  data/processed/base_weekly_v3_chik.parquet    <- base_weekly_v3.parquet (TFT)
  data/processed/season_targets_v3_chik.parquet <- + reajuste de Richards, mesma regra do v3

Uso (a partir de src/):  python preprocess_chik.py [base_v3]
  base_v3: só a base do TFT (para rodar no servidor, que já tem base_weekly_v3.parquet).
"""
import sys
import numpy as np
import pandas as pd

import preprocess as P
import preprocess_v3 as P3

PROC = P3.PROC


def load_chik():
    chik = P3.load_chik()
    return chik[chik["date"] <= P.LAST_DATE]


def swap(base, chik):
    """casos e incidência passam a ser de chikungunya; devolve também os casos de dengue de cada linha."""
    start = chik["date"].min()
    n = base["date"].ge(start).sum()
    b = base[base["date"] >= start].merge(chik, on=["geocode", "date"], how="left")
    assert len(b) == n and b["casos_chik"].notna().all(), "semana sem dado de chikungunya depois do início da série"
    dengue = b["casos"].to_numpy(float)
    b["casos"] = b.pop("casos_chik").astype(base["casos"].dtype)
    b["incidence"] = (b["casos"] / b["population"] * 1e5).astype(base["incidence"].dtype)
    return b.sort_values(["geocode", "date"]).reset_index(drop=True), dengue


def build_base_v3(chik):
    base = pd.read_parquet(f"{PROC}/base_weekly_v3.parquet")
    b, dengue = swap(base, chik)
    b["log_casos_chik"] = np.log1p(np.clip(dengue, 0, None)).astype(base["log_casos_chik"].dtype)
    b.to_parquet(f"{PROC}/base_weekly_v3_chik.parquet", index=False)
    print("base v3 chik:", b.shape, b["date"].min().date(), "->", b["date"].max().date(), flush=True)


def main(only_v3=False):
    chik = load_chik()
    print("chikungunya:", chik["date"].min().date(), "->", chik["date"].max().date(), flush=True)
    build_base_v3(chik)
    if only_v3:
        return
    base, _ = swap(pd.read_parquet(f"{PROC}/base_weekly.parquet"), chik)
    base.to_parquet(f"{PROC}/base_weekly_chik.parquet", index=False)
    print("base chik:", base.shape, flush=True)
    targets = P.build_season_targets(base, disease="chikungunya")
    print(targets.groupby("season").agg(municipios=("geocode", "size"), com_ajuste=("has_fit", "sum")).to_string(), flush=True)
    targets.to_parquet(f"{PROC}/season_targets_chik.parquet", index=False)
    P3.refit_targets(base, src=f"{PROC}/season_targets_chik.parquet", dst=f"{PROC}/season_targets_v3_chik.parquet")


if __name__ == "__main__":
    main(only_v3=sys.argv[1:] == ["base_v3"])
