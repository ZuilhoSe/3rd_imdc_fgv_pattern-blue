"""
Pattern Blue v4 — acrescenta à base v3:
  1. previsão climática sazonal emitida em junho de cada ano (a última antes do corte EW25):
     fc_pre_*   = média dos meses à frente 1-3 (jul-set, antes da temporada)
     fc_early_* = média dos meses à frente 4-6 (out-dez, início da temporada prevista)
     A fonte só vai até 6 meses à frente: os meses de pico (fev-mai) não têm previsão.
  2. temporada em curso de forma explícita:
     cum_log_casos, cum_log_incidence = acumulado da temporada até a semana
     prev_season_log_total             = total da temporada anterior, já completa
Saída: data/processed/base_weekly_v4.parquet
"""
import os
import numpy as np
import pandas as pd

RAW, PROC = "../data/raw", "../data/processed"
VARS = {"temp_med": "temp", "umid_med": "umid", "precip_tot": "precip"}


def seasonal_forecast():
    old = pd.read_csv(f"{RAW}/forecasting_climate.csv.gz")
    new = pd.read_csv(f"{RAW}/forecasting_climate_update_2026.csv.gz").rename(columns={"rel_umid_med": "umid_med"})
    for d in (old, new):
        d["reference_month"] = pd.to_datetime(d["reference_month"], format="mixed")
    df = pd.concat([old[old["reference_month"] < new["reference_month"].min()], new], ignore_index=True)
    df = df[df["reference_month"].dt.month == 6].copy()
    df["year"] = df["reference_month"].dt.year
    df["periodo"] = np.where(df["forecast_months_ahead"] <= 3, "pre", "early")
    g = df.groupby(["geocode", "year", "periodo"])[list(VARS)].mean().unstack("periodo")
    g.columns = [f"fc_{p}_{VARS[v]}" for v, p in g.columns]
    return g.reset_index()


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    base = pd.read_parquet(f"{PROC}/base_weekly_v3.parquet")
    base = base.sort_values(["geocode", "date"]).reset_index(drop=True)

    fc = seasonal_forecast()
    cols = [c for c in fc.columns if c.startswith("fc_")]
    base = base.merge(fc, on=["geocode", "year"], how="left")
    print("anos com previsão de junho:", fc["year"].min(), "-", fc["year"].max(), "| faltando:", base[cols].isna().mean().round(4).to_dict())
    base[cols] = base.groupby("geocode")[cols].ffill().bfill()   # 2010: anos sem emissão de junho anterior

    cum = base.groupby(["geocode", "season"])["casos"].cumsum().clip(lower=0)
    base["cum_log_casos"] = np.log1p(cum)
    base["cum_log_incidence"] = np.log1p(cum / base["population"] * 1e5)
    tot = base.groupby(["geocode", "season"])["casos"].sum().rename("prev_total").reset_index()
    tot["season"] += 1
    base = base.merge(tot, on=["geocode", "season"], how="left")
    base["prev_season_log_total"] = np.log1p(base["prev_total"].clip(lower=0)).fillna(0.0)
    base = base.drop(columns="prev_total").sort_values(["geocode", "date"]).reset_index(drop=True)

    new_cols = cols + ["cum_log_casos", "cum_log_incidence", "prev_season_log_total"]
    f = base[base["date"] == base["date"].max()]
    print(f"{len(base):,} linhas | {base.shape[1]} colunas | NaN nas novas: {int(base[new_cols].isna().sum().sum())}")
    print(f[new_cols].describe().T.round(3).to_string())
    base.to_parquet(f"{PROC}/base_weekly_v4.parquet", index=False)


if __name__ == "__main__":
    main()
