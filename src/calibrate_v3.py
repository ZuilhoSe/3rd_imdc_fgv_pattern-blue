"""
Pattern Blue v3 — calibração dos intervalos sem retreinar: A (conformal), B (ruído de observação),
C (conjunto full + best) e combinações. Protocolo: docs/evaluation_protocol_v3_calib.md

Uso (a partir de src/):
  python calibrate_v3.py dispersion        # estima k da binomial negativa por corte
  python calibrate_v3.py sims [anos...]    # gera v3, v3B, v3C, v3BC
  python calibrate_v3.py conformal         # aplica A sobre as quatro -> v3A, v3AB, v3AC, v3ABC
  python calibrate_v3.py report            # tabelas em reports/v3_calib/
Nada aqui envia dados à plataforma.
"""
import glob
import json
import os
import sys
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.stats import nbinom

import build_submissions as B
import common as C
import common_v3 as V
import evaluate_v3 as E
import imdc_submission as S
import rolling_eval as R

OUT = "outputs/v3/frames_calib"
REPORT = "../reports/v3_calib"
DISP_PATH = f"{OUT}/dispersion.json"
YEARS = list(range(2015, 2027))          # 2026 = previsão final (sem verdade)
SIMS = {"v3": (False, False), "v3B": (True, False), "v3C": (False, True), "v3BC": (True, True)}  # (ruído B, conjunto C)
CAL = {"v3A": "v3", "v3AB": "v3B", "v3AC": "v3C", "v3ABC": "v3BC"}
VARIANTS = ["v3", "v3A", "v3B", "v3C", "v3AB", "v3AC", "v3BC", "v3ABC"]
COLS = S.INTERVAL_ORDER
QS = C.QUANTILE_LEVELS
SELECT_YEARS = list(range(2017, 2022))
D_CITY, D_STATE = 3000, 1000


# ------------------------------------------------------------- B: dispersão
def estimate_dispersion():
    t = pd.read_parquet(V.TARGETS_PATH)
    base = pd.read_parquet("../data/processed/base_weekly_v3.parquet", columns=["geocode", "date", "season", "casos"])
    base["geocode"] = base["geocode"].astype(str)
    t["geocode"] = t["geocode"].astype(str)
    base = base.sort_values(["geocode", "date"])
    base["w"] = base.groupby(["geocode", "season"]).cumcount()
    out = {}
    for year in YEARS:
        # temporada da base s = EW41/(s-1) a EW40/s; terminar até a EW40 de Y-1 -> s <= Y-1
        cand = t[t["has_fit"] & (t["season"] <= year - 1)]
        cand = cand.sample(min(len(cand), 4000), random_state=0)
        ys, mus = [], []
        for s, g in cand.groupby("season"):
            W = len(S.season_weeks(s - 1))
            obs = base[(base["season"] == s) & base["geocode"].isin(g["geocode"])]
            wide = obs.pivot(index="geocode", columns="w", values="casos")
            if wide.shape[1] != W:
                continue
            g = g.set_index("geocode").loc[wide.index]
            mu = S.weekly_curves(s - 1, g["obs_total"], g["alpha"], g["beta"], g["peak_idx"])
            ok = ~wide.isna().any(axis=1).to_numpy()
            ys.append(wide.to_numpy(float)[ok].ravel()); mus.append(mu[ok].ravel())
        y, mu = np.concatenate(ys), np.clip(np.concatenate(mus), 1e-6, None)

        def nll(lk):
            k = np.exp(lk)
            return -nbinom.logpmf(y, k, k / (k + mu)).sum()

        res = minimize_scalar(nll, bounds=(-4, 8), method="bounded")
        out[year] = float(np.exp(res.x))
        print(f"corte {year}: k = {out[year]:.3f} | {len(y):,} semanas", flush=True)
    os.makedirs(OUT, exist_ok=True)
    with open(DISP_PATH, "w") as f:
        json.dump(out, f, indent=1)


# ------------------------------------------------------------- B e C: simulação
def params_for(year):
    if year == 2026:
        return {v: f"{V.PARAMS_DIR}/params_final_{v}.parquet" for v in ["full", "best"]}
    p = E.params_paths(year)
    return {"full": p["tft_v3"], "best": p["tft_v3_best"]}


def draws(pqs, D, seed, rho):
    parts = [S.sample_params(pq, QS, D // len(pqs), seed + i, rho) for i, pq in enumerate(pqs)]
    return {p: np.concatenate([x[p] for x in parts], axis=1) for p in S.PARAMS}


def noisy(curves, k, rng):
    return curves if k is None else rng.poisson(rng.gamma(k, curves / k)).astype(float)


def city_frame(rows_list, gc, year, k):
    pqs = [{p: np.asarray(r[gc][p], float)[None, :] for p in S.PARAMS} for r in rows_list]
    s = draws(pqs, D_CITY, 0, 0.0)
    curves = S.weekly_curves(year, s["total_cases"][0], s["alpha"][0], s["beta"][0], s["peak_week"][0])
    curves = noisy(curves, k, np.random.default_rng(int(gc)))
    return S.build_df(year, S._quantile_matrix(curves))


def state_frame(rows_list, gcs, year, rho, k):
    s = draws([B.stack(r, gcs) for r in rows_list], D_STATE, 0, rho)
    rng = np.random.default_rng(int(gcs[0]))
    total = np.zeros((D_STATE, len(S.season_weeks(year))))
    for m in range(len(gcs)):
        total += noisy(S.weekly_curves(year, s["total_cases"][m], s["alpha"][m], s["beta"][m], s["peak_week"][m]), k, rng)
    return S.build_df(year, S._quantile_matrix(total))


def path(model, year, level, rho=None):
    return f"{OUT}/{model}_{year}_{level}_{rho}.parquet"


def write_sims(years):
    with open(DISP_PATH) as f:
        disp = {int(y): k for y, k in json.load(f).items()}
    for year in years:
        rows = {v: E.read_rows(p) for v, p in params_for(year).items()}
        ufs = B.by_uf(rows["full"])
        for model, (use_b, use_c) in SIMS.items():
            rl = [rows["full"], rows["best"]] if use_c else [rows["full"]]
            k = disp[year] if use_b else None
            if not os.path.exists(path(model, year, "city")):
                f = {gc: city_frame(rl, gc, year, k) for gc in B.DENGUE_CITIES}
                pd.concat([d.assign(unit=u) for u, d in f.items()], ignore_index=True).to_parquet(path(model, year, "city"), index=False)
            for rho in E.RHOS:
                if os.path.exists(path(model, year, "state", rho)):
                    continue
                f = {uf: state_frame(rl, gcs, year, rho, k) for uf, gcs in sorted(ufs.items())}
                pd.concat([d.assign(unit=u) for u, d in f.items()], ignore_index=True).to_parquet(path(model, year, "state", rho), index=False)
            print(f"{model} {year} ok", flush=True)


# ------------------------------------------------------------- A: conformal
def calibrate(frame, past):
    out = frame.copy()
    if past is None or past.empty:
        return out
    ly = np.log1p(past["casos"].to_numpy(float))
    lg = lambda d, c: np.log1p(np.clip(d[c].to_numpy(float), 0, None))
    n = len(ly)
    for k in E.INTERVALS:
        a = 1 - int(k) / 100
        lev = min(1.0, np.ceil((n + 1) * (1 - a / 2)) / n)
        q_lo = np.quantile(lg(past, f"lower_{k}") - ly, lev, method="higher")
        q_hi = np.quantile(ly - lg(past, f"upper_{k}"), lev, method="higher")
        out[f"lower_{k}"] = np.expm1(lg(frame, f"lower_{k}") - q_lo)
        out[f"upper_{k}"] = np.expm1(lg(frame, f"upper_{k}") + q_hi)
    out["pred"] = np.expm1(lg(frame, "pred") + np.median(ly - lg(past, "pred")))
    out[COLS] = np.sort(np.clip(out[COLS].to_numpy(float), 0, None), axis=1)
    return out


def write_conformal():
    truth = E.load_truth()
    for model, src in CAL.items():
        for level, rhos in [("city", [None]), ("state", E.RHOS)]:
            for rho in rhos:
                frames = {y: pd.read_parquet(path(src, y, level, rho)) for y in YEARS}
                with_truth = {y: f.assign(date=pd.to_datetime(f["date"])).merge(truth[level][["unit", "date", "casos"]], on=["unit", "date"])
                              for y, f in frames.items() if y <= 2025}
                for y in YEARS:
                    past = [with_truth[p] for p in with_truth if p <= y - 2]
                    calibrate(frames[y], pd.concat(past) if past else None).to_parquet(path(model, y, level, rho), index=False)
        print(f"{model} ok", flush=True)


# ------------------------------------------------------------- relatório
def scores(truth):
    rows = []
    files = glob.glob(f"{OUT}/*.parquet") + glob.glob(f"{E.OUT}/frames/b3_*.parquet") + glob.glob(f"{E.OUT}/frames/tft_v3_[0-9]*.parquet")
    for p in sorted(files):
        model, year, level, rho = os.path.basename(p)[:-8].rsplit("_", 3)
        if int(year) > 2025:
            continue
        s = E.score(pd.read_parquet(p), truth[level])
        rows.append(s.assign(model=model, cut_year=int(year), level=level, rho=None if rho == "None" else float(rho)))
    return pd.concat(rows, ignore_index=True)


def forecast_sums(chosen):
    rows = []
    for m in VARIANTS:
        rho = chosen.get((m, 2026), E.DEFAULT_RHO)
        for level, r in [("city", None), ("state", rho)]:
            f = pd.read_parquet(path(m, 2026, level, r))
            rows.append({"modelo": m, "nivel": level, "rho": r, "soma_medianas": f["pred"].sum(),
                         "soma_upper_90": f["upper_90"].sum(), "soma_lower_90": f["lower_90"].sum()})
    return pd.DataFrame(rows)


def report():
    os.makedirs(REPORT, exist_ok=True)
    pd.set_option("display.width", 220, "display.max_columns", 30, "display.max_rows", 120)
    truth = E.load_truth()
    sc = scores(truth)
    chosen = E.select_rho(sc)
    sel = E.apply_rho(sc, chosen)
    pd.Series({f"{m}|{y}": r for (m, y), r in chosen.items() if m in VARIANTS}, name="rho").to_csv(f"{REPORT}/rho_by_cut.csv")

    # escolha pré-registrada: 2017-2021 contra o B3, média do log entre níveis
    rel_sel = R.relative_table(sel[sel["cut_year"].isin(SELECT_YEARS)], ref="b3")
    rel_sel = rel_sel[rel_sel["modelo"].isin(VARIANTS)]
    rel_sel.to_csv(f"{REPORT}/selection_2017_2021.csv", index=False)
    pick = np.exp(np.log(rel_sel.pivot(index="modelo", columns="nivel", values="wis_rel")).mean(axis=1)).sort_values()
    print("Escolha (2017-2021, WIS relativo ao B3, média geométrica entre níveis)\n", pick.round(3).to_string())
    print("\nvariante escolhida:", pick.index[0])

    off = E.official_scores(truth)
    all_sc = pd.concat([sel, off], ignore_index=True)
    show_extra = {"state": [E.BASELINE["state"], E.SUBMITTED_V1, "3rd_imdc_emap_lstm", "3rd_imdc_lncc_lncc_arp26_dengue", "b3", "tft_v3"],
                  "city": [E.BASELINE["city"], E.SUBMITTED_V1, "3rd_imdc_emap_epidematicos_prophet_fixed", "b3", "tft_v3"]}
    for level in ["state", "city"]:
        tab, _ = E.ratio_table(all_sc, level, [])
        tab["posicao_entre_oficiais"] = [int((tab.loc[~tab.index.isin(VARIANTS + ["b3", "b3_v3", "tft_v3"]), "R"] < r).sum()) + 1 for r in tab["R"]]
        keep = tab[tab.index.isin(VARIANTS + show_extra[level])]
        keep.to_csv(f"{REPORT}/official_ratio_{level}.csv")
        print(f"\nRazão oficial contra {E.BASELINE[level]} ({level})\n", keep.round(3).to_string())
        iv = E.intervals_table(all_sc, level, show_extra[level][:2] + VARIANTS)
        iv.to_csv(f"{REPORT}/intervals_{level}.csv")
        print(f"\nIntervalos, 4 validações ({level})\n", iv.round(1).to_string())
    for name, yrs in [("2015_2024", range(2015, 2025)), ("2017_2024", range(2017, 2025))]:
        rol = R.relative_table(sel[sel["cut_year"].isin(yrs)], ref="b3")
        rol = rol[rol["modelo"].isin(VARIANTS + ["tft_v3"])]
        rol.to_csv(f"{REPORT}/rolling_{name}.csv", index=False)
        print(f"\nOrigem móvel {name}, relativo ao B3\n", rol.round(3).to_string(index=False))
    roll_cov = sel[sel["cut_year"].isin(range(2017, 2025)) & sel["model"].isin(VARIANTS)].groupby(["level", "model"])[[f"cov{k}" for k in E.INTERVALS]].mean() * 100
    roll_cov.to_csv(f"{REPORT}/rolling_coverage_2017_2024.csv")
    print("\nCobertura na origem móvel 2017-2024\n", roll_cov.round(1).to_string())
    fc = forecast_sums(chosen)
    fc.to_csv(f"{REPORT}/forecast_2026_27.csv", index=False)
    print("\nPrevisão 2026-27\n", fc.round(0).to_string(index=False))


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "dispersion":
        estimate_dispersion()
    elif cmd == "sims":
        write_sims([int(y) for y in sys.argv[2:]] or YEARS)
    elif cmd == "conformal":
        write_conformal()
    else:
        report()
