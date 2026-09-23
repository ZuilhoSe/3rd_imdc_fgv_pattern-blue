"""
IMDC 2026 — PRÉ-PROCESSAMENTO (substitui a lógica do notebook preprocess_infodengue).

Gera duas tabelas:
  data/processed/base_weekly.parquet     -> uma linha por (geocode, semana) com as covariáveis
  data/processed/season_targets.parquet  -> uma linha por (geocode, temporada) com os alvos

Correções em relação à versão anterior:
  * junta os arquivos *_update_2026 do FTP (dados até EW25/2026);
  * índices oceânicos (semanais) entram por data — o merge por (ano, mês) replicava
    cada linha 4-5x;
  * episcanner filtrado para dengue — o CSV mistura dengue e chikungunya e duplicava
    as linhas de novo (total 3-10x);
  * peak_week vira índice da semana dentro da temporada (EW41 = 0), e não YYYYWW;
  * municípios/temporadas sem ajuste Richards (< 50 casos ou falha) não são mais
    descartados: recebem o total observado e a forma é imputada depois (common.py).

Rode a partir de src/:  python preprocess.py
"""
import numpy as np
import pandas as pd
from epiweeks import Week

RAW = "../data/raw"
PROC = "../data/processed"
LAST_DATE = pd.Timestamp("2026-06-21")  # início da EW25/2026 — corte oficial da previsão final


def season_start(end_year):
    return pd.Timestamp(Week(end_year - 1, 41, system="cdc").startdate())


def season_end(end_year):
    return pd.Timestamp(Week(end_year, 40, system="cdc").startdate())


def season_end_year_of(epiweek):
    """temporada (ano final) a que cada semana pertence: EW41+ -> ano epidemiológico + 1."""
    ey, w = epiweek // 100, epiweek % 100
    return np.where(w >= 41, ey + 1, ey)


def load_cases():
    old = pd.read_csv(f"{RAW}/dengue.csv.gz", usecols=["geocode", "date", "casos", "epiweek", "uf"])
    new = pd.read_csv(f"{RAW}/dengue_update_2026.csv.gz", usecols=["geocode", "date", "casos", "epiweek", "uf"])
    new["date"] = pd.to_datetime(new["date"])
    old["date"] = pd.to_datetime(old["date"])
    # a atualização é mais recente (dados revisados) -> prevalece a partir da 1ª data dela
    df = pd.concat([old[old["date"] < new["date"].min()], new], ignore_index=True)
    df = df[df["date"] <= LAST_DATE]
    assert not df.duplicated(["geocode", "date"]).any()
    return df


def load_climate():
    cols = ["geocode", "date", "temp_med", "precip_med", "rel_humid_med"]
    old = pd.read_csv(f"{RAW}/climate.csv.gz", usecols=cols)
    new = pd.read_csv(f"{RAW}/climate_update_2026.csv.gz", usecols=cols)
    for d in (old, new):
        d["date"] = pd.to_datetime(d["date"])
    old = old[old["date"] >= "2009-01-01"]
    df = pd.concat([old[old["date"] < new["date"].min()], new], ignore_index=True)
    return df.drop_duplicates(["geocode", "date"], keep="last")


def load_forecast_climate():
    old = pd.read_csv(f"{RAW}/forecasting_climate.csv.gz")
    new = pd.read_csv(f"{RAW}/forecasting_climate_update_2026.csv.gz").rename(columns={"rel_umid_med": "umid_med"})
    for d in (old, new):
        d["reference_month"] = pd.to_datetime(d["reference_month"], format="mixed")
    df = pd.concat([old[old["reference_month"] < new["reference_month"].min()], new], ignore_index=True)
    valid = df["reference_month"].values.astype("datetime64[M]") + df["forecast_months_ahead"].values.astype("timedelta64[M]")
    df["year"] = pd.DatetimeIndex(valid).year
    df["month"] = pd.DatetimeIndex(valid).month
    df = df.rename(columns={"temp_med": "forecast_temp_med", "umid_med": "forecast_umid_med",
                            "precip_tot": "forecast_precip_tot"})
    return (df.groupby(["geocode", "year", "month"])[["forecast_temp_med", "forecast_umid_med", "forecast_precip_tot"]]
              .mean().reset_index())


def build_base():
    print("casos...")
    df = load_cases()
    df = df.sort_values(["geocode", "date"]).reset_index(drop=True)
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["time_idx"] = ((df["date"] - df["date"].min()).dt.days // 7).astype(int)
    df["week_of_year"] = (df["epiweek"] % 100).astype(int)
    df["week_cycle"] = np.where(df["week_of_year"] >= 41, df["week_of_year"] - 40, df["week_of_year"] + 12)
    df["sin_week_cycle"] = np.sin(2 * np.pi * df["week_cycle"] / 52)
    df["cos_week_cycle"] = np.cos(2 * np.pi * df["week_cycle"] / 52)
    df["season"] = season_end_year_of(df["epiweek"].astype(int))

    print("clima...")
    clim = load_climate()
    df = df.merge(clim, on=["geocode", "date"], how="left")
    df[["temp_med", "precip_med", "rel_humid_med"]] = df.groupby("geocode")[["temp_med", "precip_med", "rel_humid_med"]].ffill()

    print("oceano (por data)...")
    oc = pd.concat([pd.read_csv(f"{RAW}/ocean_climate_oscillations.csv.gz"),
                    pd.read_csv(f"{RAW}/ocean_climate_oscillations_update_2026.csv.gz")], ignore_index=True)
    oc["date"] = pd.to_datetime(oc["date"])
    oc = oc[["date", "enso", "iod", "pdo"]].drop_duplicates("date", keep="last").sort_values("date")
    df = pd.merge_asof(df.sort_values("date"), oc, on="date", direction="backward").sort_values(["geocode", "date"])

    print("previsão climática...")
    fc = load_forecast_climate()
    df = df.merge(fc, on=["geocode", "year", "month"], how="left")
    fcols = ["forecast_temp_med", "forecast_umid_med", "forecast_precip_tot"]
    df[fcols] = df.groupby("geocode")[fcols].ffill()

    print("população...")
    pop = pd.read_csv(f"{RAW}/datasus_population_2001_2025.csv.gz")
    df = df.merge(pop, on=["geocode", "year"], how="left")
    df["population"] = df.groupby("geocode")["population"].ffill()  # 2026 = 2025
    df["log_pop"] = np.log1p(df["population"])
    df["incidence"] = df["casos"] / df["population"] * 1e5

    print("estáticas...")
    env = pd.read_csv(f"{RAW}/environ_vars.csv.gz", encoding="latin-1")[["geocode", "koppen", "biome"]]
    reg = pd.read_csv(f"{RAW}/map_regional_health.csv")[["geocode", "macroregion_name", "regional_geocode"]]
    df = df.merge(env, on="geocode", how="left").merge(reg, on="geocode", how="left")

    df = df.sort_values(["geocode", "date"]).reset_index(drop=True)
    assert not df.duplicated(["geocode", "date"]).any(), "linhas duplicadas!"
    # climatologia por município p/ buracos remanescentes no início das séries
    for c in ["temp_med", "precip_med", "rel_humid_med"] + fcols:
        df[c] = df[c].fillna(df.groupby("geocode")[c].transform("mean")).fillna(df[c].mean())
    df["regional_geocode"] = df["regional_geocode"].astype(str)
    return df


def build_season_targets(base):
    """total observado por (município, temporada) + parâmetros Richards (quando houver)."""
    obs = base.groupby(["geocode", "season"]).agg(obs_total=("casos", "sum"), n_weeks=("casos", "size")).reset_index()
    # só temporadas completas (52/53 semanas) viram alvo
    obs = obs[obs["n_weeks"] >= 52].drop(columns="n_weeks")

    epi = pd.read_csv(f"{PROC}/episcanner_results_2026.csv")
    epi = epi[(epi["disease"] == "dengue") & (epi["success"])].rename(columns={"season_end_year": "season"})
    # peak_week (YYYYWW) -> índice na temporada (0 = EW41 do ano anterior)
    peak_date = epi["peak_week"].astype(int).astype(str).map(lambda s: pd.Timestamp(Week.fromstring(s, system="cdc").startdate()))
    start = epi["season"].map(season_start)
    epi["peak_idx"] = ((peak_date - start).dt.days // 7).astype(float)
    epi = epi[["geocode", "season", "alpha", "beta", "peak_idx"]]

    t = obs.merge(epi, on=["geocode", "season"], how="left")
    t["has_fit"] = t["alpha"].notna()
    print(f"temporadas-alvo: {len(t)} | com ajuste Richards: {t['has_fit'].sum()}")
    return t


def main():
    base = build_base()
    print(f"base: {base.shape} | municípios {base.geocode.nunique()} | {base.date.min().date()} -> {base.date.max().date()}")
    targets = build_season_targets(base)
    base.to_parquet(f"{PROC}/base_weekly.parquet", index=False)
    targets.to_parquet(f"{PROC}/season_targets.parquet", index=False)
    print("salvo.")


if __name__ == "__main__":
    main()
