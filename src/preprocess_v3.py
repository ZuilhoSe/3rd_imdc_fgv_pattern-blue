"""
Pattern Blue v3 — base com TODOS os dados disponíveis no FTP do desafio.

Parte das tabelas da versão submetida (base_weekly / season_targets), que ficam intactas, e gera:
  data/processed/base_weekly_v3.parquet     -> + clima completo, chikungunya e acessos Afya
  data/processed/season_targets_v3.parquet  -> + reajuste Richards das temporadas >= 50 casos sem ajuste

Rode a partir de src/:  python preprocess_v3.py
"""
import warnings
import lmfit as lm
import numpy as np
import pandas as pd
from lmfit import Parameters

warnings.filterwarnings("ignore")
RAW = "../data/raw"
PROC = "../data/processed"
EXTRA_CLIMATE = ["temp_min", "temp_max", "precip_min", "precip_max", "pressure_med",
                 "rel_humid_min", "rel_humid_max", "thermal_range", "rainy_days"]


def load_extra_climate():
    new = pd.read_csv(f"{RAW}/climate_update_2026.csv.gz", usecols=["geocode", "date"] + EXTRA_CLIMATE, parse_dates=["date"])
    parts = []
    reader = pd.read_csv(f"{RAW}/climate.csv.gz", usecols=["geocode", "date"] + EXTRA_CLIMATE,
                         parse_dates=["date"], chunksize=2_000_000)
    for chunk in reader:
        chunk = chunk[(chunk["date"] >= "2009-01-01") & (chunk["date"] < new["date"].min())]
        parts.append(chunk.astype({c: "float32" for c in EXTRA_CLIMATE}))
    out = pd.concat(parts + [new.astype({c: "float32" for c in EXTRA_CLIMATE})], ignore_index=True)
    return out.drop_duplicates(["geocode", "date"], keep="last")


def load_chik():
    old = pd.read_csv(f"{RAW}/chikungunya.csv.gz", usecols=["geocode", "date", "casos"], parse_dates=["date"])
    new = pd.read_csv(f"{RAW}/chikungunya_update_2026.csv.gz", usecols=["geocode", "date", "casos"], parse_dates=["date"])
    df = pd.concat([old[old["date"] < new["date"].min()], new], ignore_index=True)
    return df.drop_duplicates(["geocode", "date"], keep="last").rename(columns={"casos": "casos_chik"})


def load_access():
    """acessos diários a páginas de dengue (Afya, 2021+) -> soma na semana epidemiológica (domingo)."""
    a = pd.read_csv(f"{RAW}/access_afya_dengue_2021_2026.csv.gz", usecols=["access_date", "geocode", "access_count"],
                    parse_dates=["access_date"])
    a["date"] = a["access_date"] - pd.to_timedelta((a["access_date"].dt.dayofweek + 1) % 7, unit="D")
    a["access_count"] = a["access_count"].fillna(0)
    # só semanas completas: a última semana parcial do arquivo sairia subestimada
    last_full = a["access_date"].max() - pd.Timedelta(days=6)
    a = a[a["date"] <= last_full]
    return a.groupby(["geocode", "date"], as_index=False)["access_count"].sum()


def extend_base():
    base = pd.read_parquet(f"{PROC}/base_weekly.parquet")
    n = len(base)
    print("clima completo...", flush=True)
    base = base.merge(load_extra_climate(), on=["geocode", "date"], how="left")
    base = base.sort_values(["geocode", "date"]).reset_index(drop=True)
    base[EXTRA_CLIMATE] = base.groupby("geocode")[EXTRA_CLIMATE].ffill()
    print("faltantes após ffill:", base[EXTRA_CLIMATE].isna().mean().round(4).to_dict(), flush=True)
    for c in EXTRA_CLIMATE:
        base[c] = base[c].fillna(base.groupby("geocode")[c].transform("mean")).fillna(base[c].mean())

    print("chikungunya...", flush=True)
    base = base.merge(load_chik(), on=["geocode", "date"], how="left")
    print("chik faltante:", round(base["casos_chik"].isna().mean(), 4), flush=True)
    base["log_casos_chik"] = np.log1p(base["casos_chik"].fillna(0).clip(lower=0))

    print("acessos Afya...", flush=True)
    acc = load_access()
    base = base.merge(acc, on=["geocode", "date"], how="left")
    base["has_access"] = base["access_count"].notna().astype("float32")
    base["log_access"] = np.log1p(base["access_count"].fillna(0).clip(lower=0))
    print("semanas com acesso:", acc["date"].min().date(), "->", acc["date"].max().date(),
          "| fração da base:", round(base["has_access"].mean(), 3), flush=True)

    assert len(base) == n, "merge alterou o número de linhas"
    base = base.drop(columns=["casos_chik", "access_count"])
    fl = base.select_dtypes("float64").columns
    base[fl] = base[fl].astype("float32")
    base.to_parquet(f"{PROC}/base_weekly_v3.parquet", index=False)
    print("base v3:", base.shape, flush=True)
    return base


def richards(L, a, b, t, tj):
    return L - L * (1 + a * np.exp(b * (t - tj))) ** (-1 / a)


def objective(params, y):
    p = params.valuesdict()
    t = np.arange(len(y))
    return (y - richards(p["L1"], p["a1"], p["b1"], t, p["tp1"])) ** 2 / len(y)


def fit_richards(weekly):
    """mesma especificação do notebook apply_2026, agora com o método realmente evolução diferencial."""
    y = np.cumsum(weekly, dtype=float)
    p = Parameters()
    p.add("gamma", min=0.3, max=0.33)
    p.add("L1", min=1.0, max=1.2 * y[-1])
    p.add("tp1", min=5, max=35)
    p.add("b1", min=1e-6, max=1)
    p.add("a1", expr="b1/(gamma + b1)", min=0.001, max=1)
    r = lm.minimize(objective, p, args=(y,), method="differential_evolution", seed=42)
    v = r.params
    fitted = richards(v["L1"].value, v["a1"].value, v["b1"].value, np.arange(len(y)), v["tp1"].value)
    r2 = 1 - np.sum((y - fitted) ** 2) / np.sum((y - y.mean()) ** 2)
    return dict(alpha=v["a1"].value, beta=v["b1"].value / v["a1"].value, tp=v["tp1"].value, r2=r2)


def refit_targets(base):
    t = pd.read_parquet(f"{PROC}/season_targets.parquet")
    t["refit"] = False
    todo = t[(~t["has_fit"]) & (t["obs_total"] >= 50)]
    print(f"\nreajustando {len(todo)} temporadas sem ajuste e com >= 50 casos", flush=True)
    for i, r in todo.iterrows():
        obs = base[(base["geocode"] == r["geocode"]) & (base["season"] == r["season"])].sort_values("date")["casos"].to_numpy(float)
        f = fit_richards(obs)
        print(f"  {r['geocode']} {r['season']} casos={int(r['obs_total'])} pico_obs={int(np.argmax(obs))} "
              f"t_p={f['tp']:.1f} alpha={f['alpha']:.3f} beta={f['beta']:.3f} R2={f['r2']:.4f}", flush=True)
        if f["r2"] >= 0.95:
            t.loc[i, ["alpha", "beta", "peak_idx"]] = [f["alpha"], f["beta"], float(round(f["tp"]))]
            t.loc[i, "has_fit"] = True
            t.loc[i, "refit"] = True
    print("reajustadas:", int(t["refit"].sum()), "| com ajuste agora:", int(t["has_fit"].sum()), flush=True)
    t.to_parquet(f"{PROC}/season_targets_v3.parquet", index=False)


if __name__ == "__main__":
    refit_targets(extend_base())
