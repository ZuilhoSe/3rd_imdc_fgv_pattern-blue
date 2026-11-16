"""
Confirmatório B do protocolo congelado (seção 6; emendas E4, E5 e E6): o C2 em chikungunya.

C2 = média de quantis de B2, B3 e C1 (C1 = média das sementes 1, 2 e 3 do v3), cortes EW25 de 2017 a 2024.
Critério de ganho, nas UFs:
  1. WIS relativo ao B3 < 1;
  2. teste de permutação de sinais, unilateral, sobre o log da razão por temporada, p < 0,10;
  3. 1 - WIS relativo > desvio entre sementes (E5: desvio padrão, ddof=1, do WIS relativo dos C2 de cada semente).

Uso (a partir de src/, sempre com DOENCA=chik):
  python confirmatorio_chik.py baselines   # B2 (previsão direta) e parâmetros do B3
  python confirmatorio_chik.py frames      # previsões semanais de B3, sementes, C1, C2 e C2 por semente
  python confirmatorio_chik.py score       # pontua UMA vez (seção 6) e grava reports/confirmatorio_chik/
"""
import itertools
import os
import sys
import numpy as np
import pandas as pd

import common as C

assert C.DOENCA == "chik", "rode com DOENCA=chik"

import build_submissions as B
import common_v3 as V
import evaluate_v3 as E
import rolling_eval as R

YEARS = list(range(2017, 2025))
SEEDS = [1, 2, 3]
SEED_MODELS = [f"tft_v3_s{s}" for s in SEEDS]
OUT = "outputs/v3_chik"
REPORT = "../reports/confirmatorio_chik"
LEVELS = [("city", None)] + [("state", r) for r in E.RHOS]


def frame_path(model, year, level, rho):
    return f"{OUT}/frames/{model}_{year}_{level}_{rho}.parquet"


def b2_path(year, level):
    return f"{R.OUT}/direct/b2_{year}_{level}.parquet"


def b3_path(year):
    return f"{B.PARAMS_DIR}/params_b3_{year}.parquet"


def baselines():
    os.makedirs(f"{R.OUT}/direct", exist_ok=True)
    os.makedirs(B.PARAMS_DIR, exist_ok=True)
    targets = pd.read_parquet(C.TARGETS_PATH)
    truth = R.load_truth()
    for year in YEARS:
        if not os.path.exists(b3_path(year)):
            R.b3_params(year, targets).to_parquet(b3_path(year), index=False)
        for level, df in truth.items():
            if not os.path.exists(b2_path(year, level)):
                f = R.b2_frames(df, year)
                pd.concat([d.assign(unit=u) for u, d in f.items()], ignore_index=True).to_parquet(b2_path(year, level), index=False)
        print(f"baselines {year} ok", flush=True)


def param_models(year):
    tag = C.SEASON_TAGS[year]
    out = {"b3": b3_path(year)}
    out |= {m: f"{V.PARAMS_DIR}/params_{tag}_s{s}_full.parquet" for m, s in zip(SEED_MODELS, SEEDS)}
    return out


def frames():
    os.makedirs(f"{OUT}/frames", exist_ok=True)
    for year in YEARS:
        for model, path in param_models(year).items():
            if not os.path.exists(path):
                print(f"falta {path}", flush=True)
                continue
            todo = [(lv, r) for lv, r in LEVELS if not os.path.exists(frame_path(model, year, lv, r))]
            if not todo:
                continue
            rows = E.read_rows(path)
            assert len(rows) == B.N_MUNICIPIOS
            for level, rho in todo:
                f = B.city_frames(rows, year) if level == "city" else B.state_frames(rows, year, rho)
                pd.concat([d.assign(unit=u) for u, d in f.items()], ignore_index=True).to_parquet(
                    frame_path(model, year, level, rho), index=False)
            print(f"{model} {year} ok", flush=True)
        for level, rho in LEVELS:
            E.average_frames([frame_path(m, year, level, rho) for m in SEED_MODELS], frame_path("c1", year, level, rho))
            base = [b2_path(year, level), frame_path("b3", year, level, rho)]
            E.average_frames(base + [frame_path("c1", year, level, rho)], frame_path("c2", year, level, rho))
            for m, s in zip(SEED_MODELS, SEEDS):   # E5: C2 de cada semente
                E.average_frames(base + [frame_path(m, year, level, rho)], frame_path(f"c2-s{s}", year, level, rho))
        print(f"combinações {year} ok", flush=True)


def expected_frames():
    models = ["b3", "c1", "c2"] + SEED_MODELS + [f"c2-s{s}" for s in SEEDS]
    paths = [frame_path(m, y, lv, r) for m in models for y in YEARS for lv, r in LEVELS]
    return paths + [b2_path(y, lv) for y in YEARS for lv in ["city", "state"]]


def sign_permutation_p(x):
    """p unilateral (H1: média < 0), exato sobre as 2^n trocas de sinal."""
    x = np.asarray(x, float)
    flips = np.array(list(itertools.product([1, -1], repeat=len(x))))
    stats = (flips * x).mean(axis=1)
    return float((stats <= x.mean() + 1e-12).mean())


def per_season_log_ratio(sel, model, level="state", ref="b3"):
    per = sel[sel["level"] == level].groupby(["model", "cut_year", "unit"], as_index=False)["wis"].mean()
    wide = per.pivot_table(index=["cut_year", "unit"], columns="model", values="wis")
    lr = (np.log(wide[model] + 1) - np.log(wide[ref] + 1)).dropna()
    return lr.groupby("cut_year").mean()


def score():
    missing = [p for p in expected_frames() if not os.path.exists(p)]
    assert not missing, f"{len(missing)} previsões faltando, por exemplo {missing[:3]}"
    assert not os.path.exists(f"{REPORT}/criterio.csv"), "o confirmatório já foi pontuado (seção 6: uma única vez)"
    os.makedirs(REPORT, exist_ok=True)
    truth = R.load_truth()
    rows = []
    for path in expected_frames():
        name = os.path.basename(path)[:-8]
        if name.startswith("b2_"):
            model, year, level = name.split("_")
            rho = None
        else:
            model, year, level, rho = name.rsplit("_", 3)
            rho = None if rho == "None" else float(rho)
        s = E.score(pd.read_parquet(path), truth[level])
        rows.append(s.assign(model=model, cut_year=int(year), level=level, rho=rho))
    sc = pd.concat(rows, ignore_index=True)
    chosen = E.select_rho(sc)
    sel = E.apply_rho(sc, chosen)
    sel.to_parquet(f"{REPORT}/scores_selecionados.parquet", index=False)

    rel = R.relative_table(sel)
    rel.to_csv(f"{REPORT}/wis_relativo.csv", index=False)
    seasons = pd.DataFrame({m: np.exp(per_season_log_ratio(sel, m)) for m in sorted(sel["model"].unique())})
    seasons.to_csv(f"{REPORT}/wis_relativo_por_temporada_uf.csv")
    comp = sel.groupby(["level", "model"])[["wis", "dispersion", "under", "over", "cov50", "cov80", "cov90", "cov95"]].mean()
    comp.to_csv(f"{REPORT}/componentes_cobertura.csv")
    pd.Series({f"{m}|{y}": r for (m, y), r in chosen.items() if y in YEARS}, name="rho").to_csv(f"{REPORT}/rho_por_corte.csv")

    st = rel[rel["nivel"] == "state"].set_index("modelo")["wis_rel"]
    wis_rel = float(st["c2"])
    p = sign_permutation_p(per_season_log_ratio(sel, "c2"))
    seeds = [float(st[f"c2-s{s}"]) for s in SEEDS]
    dp = float(np.std(seeds, ddof=1))
    crit = pd.DataFrame([
        {"condicao": "1. WIS relativo ao B3 < 1", "valor": wis_rel, "limiar": 1.0, "vale": wis_rel < 1},
        {"condicao": "2. permutação de sinais, unilateral, p < 0,10", "valor": p, "limiar": 0.10, "vale": p < 0.10},
        {"condicao": "3. 1 - WIS relativo > desvio entre sementes (E5)", "valor": 1 - wis_rel, "limiar": dp, "vale": (1 - wis_rel) > dp},
    ])
    crit["temporadas"] = len(YEARS)
    crit.to_csv(f"{REPORT}/criterio.csv", index=False)

    pd.set_option("display.width", 200, "display.max_columns", 20)
    print("\nWIS relativo ao B3, chikungunya, cortes 2017 a 2024\n", rel.round(3).to_string(index=False))
    print("\nPor temporada (UFs)\n", seasons.round(3).to_string())
    print("\nC2 por semente (UFs):", [round(v, 3) for v in seeds], "| desvio", round(dp, 4))
    print("\nCritério de ganho\n", crit.to_string(index=False))
    print("\nGANHO" if crit["vale"].all() else "\nSEM GANHO")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    {"baselines": baselines, "frames": frames, "score": score}[sys.argv[1]]()
