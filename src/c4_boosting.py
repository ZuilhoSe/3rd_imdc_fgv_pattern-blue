"""
Candidato C4 do protocolo congelado (docs/protocolo_congelado_2026-11-15.md, seção 4, emenda E2).

Gradient boosting por quantil para o log do total da temporada de cada município, com a forma (alpha, beta,
pico) do B3. Para o corte EW25/Y, a temporada prevista é a Y+1 (EW41/Y a EW40/Y+1) e só se usa o que já
existia no corte: temporadas completas até Y (a Y termina na EW40/Y, depois do corte, então a última
completa é a Y-1, como em common.season_targets_for_cut) e a temporada Y até a EW25/Y.

Treino do corte Y: cada (município, temporada S) com S <= Y-1, com as variáveis montadas como se o corte
fosse EW25/(S-1). Hiperparâmetros: os padrões do scikit-learn, fixados na emenda E2.

Uso (a partir de src/):  python c4_boosting.py [anos...]    # grava outputs/params/v3/params_c4_<Y>.parquet
"""
import os
import sys
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

import build_submissions as B
import common as C
import common_v3 as V

YEARS = list(range(2015, 2025))
CATEGORICAL = ["uf", "koppen", "biome", "macroregion_name"]
N_LAGS = 4
RECENT_WEEKS = 8
SEED = 0
FIRST_SEASON = 2011


def load():
    cols = ["geocode", "date", "casos", "season", "log_pop"] + CATEGORICAL
    base = pd.read_parquet(V.BASE_PATH, columns=cols)
    base["geocode"] = base["geocode"].astype(str)
    totals = base.groupby(["geocode", "season"])["casos"].sum().rename("total").reset_index()
    totals = totals[totals["season"] >= FIRST_SEASON]   # a 2010 começa em janeiro na base: incompleta
    targets = pd.read_parquet(V.TARGETS_PATH, columns=["geocode", "season", "obs_total"])
    targets["geocode"] = targets["geocode"].astype(str)
    static = base.drop_duplicates("geocode", keep="last").set_index("geocode")[CATEGORICAL]
    return base, totals, targets, static


def features(base, totals, static, cut_year):
    """Uma linha por município, com o que se sabia na EW25/cut_year. Prevê a temporada cut_year + 1."""
    cut = C.cut_date(cut_year)
    known = base[base["date"] <= cut]
    complete = totals[totals["season"] <= cut_year - 1].pivot(index="geocode", columns="season", values="total")
    f = pd.DataFrame(index=static.index)
    for lag in range(1, N_LAGS + 1):
        s = cut_year - lag
        f[f"log_total_lag{lag}"] = np.log1p(complete[s]) if s in complete.columns else np.nan
    hist = np.log1p(complete)
    f["log_total_mediana"] = hist.median(axis=1)
    f["log_total_max"] = hist.max(axis=1)
    f["temporadas_completas"] = hist.notna().sum(axis=1)
    current = known[known["season"] == cut_year]
    f["log_parcial_temporada"] = np.log1p(current.groupby("geocode")["casos"].sum())
    recent = known[known["date"] > cut - pd.Timedelta(weeks=RECENT_WEEKS)]
    f["log_ultimas_semanas"] = np.log1p(recent.groupby("geocode")["casos"].sum())
    f["log_pop"] = known.groupby("geocode")["log_pop"].last()
    for c in CATEGORICAL:
        f[c] = static[c].astype("category")
    return f


def fit_predict(base, totals, targets, static, year):
    rows = []
    # temporadas completas no corte Y: S <= Y-1; a partir de 2012, porque a parcial da 2011 começa na 2010
    for s in range(FIRST_SEASON + 1, year):
        f = features(base, totals, static, s - 1)
        y = targets[targets["season"] == s].set_index("geocode")["obs_total"]
        f = f.join(np.log1p(y).rename("y"), how="inner")
        rows.append(f)
    train = pd.concat(rows)
    train = train[train["y"].notna()]
    X, y = train.drop(columns="y"), train["y"].to_numpy(float)
    X = X.loc[:, X.notna().any()]        # defasagem que ainda não existe em nenhum exemplo de treino
    test = features(base, totals, static, year)
    for c in CATEGORICAL:                 # mesmas categorias no treino e na previsão
        cats = pd.api.types.union_categoricals([X[c], test[c]]).categories
        X[c] = pd.Categorical(X[c].astype(str), categories=cats)
        test[c] = pd.Categorical(test[c].astype(str), categories=cats)
    preds = []
    for q in C.QUANTILE_LEVELS:
        model = HistGradientBoostingRegressor(loss="quantile", quantile=q, categorical_features="from_dtype",
                                              random_state=SEED)
        preds.append(model.fit(X, y).predict(test[X.columns]))
    pred = np.sort(np.column_stack(preds), axis=1)    # quantis sem cruzamento
    return pd.DataFrame(np.expm1(pred).clip(min=0), index=test.index, columns=C.QUANTILE_LEVELS), len(train)


def main(years):
    base, totals, targets, static = load()
    for year in years:
        out = f"{V.PARAMS_DIR}/params_c4_{year}.parquet"
        if os.path.exists(out):
            continue
        totals_q, n = fit_predict(base, totals, targets, static, year)
        b3 = pd.read_parquet(f"{B.PARAMS_DIR}/params_b3_{year}.parquet").astype({"geocode": str})
        b3 = b3.sort_values(["geocode", "q"]).reset_index(drop=True)
        long = totals_q.stack().rename("total_c4").rename_axis(["geocode", "q"]).reset_index()
        merged = b3.merge(long, on=["geocode", "q"], how="left")
        assert len(merged) == len(b3) and merged["total_c4"].notna().all(), "município sem previsão no C4"
        merged["total_cases"] = merged.pop("total_c4")
        merged.to_parquet(out, index=False)
        print(f"c4 {year}: treino {n} linhas, mediana do total previsto {merged.loc[merged.q == 0.5, 'total_cases'].sum():,.0f}",
              flush=True)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main([int(y) for y in sys.argv[1:]] or YEARS)
