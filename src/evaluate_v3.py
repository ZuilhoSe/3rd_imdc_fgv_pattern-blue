"""
Pattern Blue v3 — avaliação com os casos observados oficiais e comparação com os baselines do IMDC.

Protocolo: docs/evaluation_protocol_v3.md. Tabelas em reports/v3/, previsões em outputs/submissions_v3/.

Uso (a partir de src/):
  python evaluate_v3.py frames [anos...]   # gera as previsões semanais dos modelos com parâmetros disponíveis
  python evaluate_v3.py report             # gera as tabelas
Nada aqui envia dados à plataforma.
"""
import glob
import os
import sys
import numpy as np
import pandas as pd

import build_submissions as B
import common as C
import common_v3 as V
import imdc_submission as S
import rolling_eval as R

EXT = "../data/external/imdc_results"
OUT = "outputs/v3"
REPORT = "../reports/v3"
SUBS = "outputs/submissions_v3"
YEARS = list(range(2015, 2026))
OFFICIAL_YEARS = {1: 2022, 2: 2023, 3: 2024, 4: 2025}
RHOS = [0.5, 0.8, 1.0]
DEFAULT_RHO = 0.5
BASELINE = {"state": "3rd_imdc_procc_bb_model", "city": "3rd_imdc_emap_lstm_muni"}
SUBMITTED_V1 = "3rd_imdc_fgv_pattern-blue"
PRIMARY = "tft_v3"
# protocolo congelado, seção 3 e emenda E1: sementes rodadas no HPC; C1 é a média de quantis delas
SEEDS = [1, 2, 3, 4, 42]
SEED_MODELS = [f"tft_v3_s{s}" for s in SEEDS]
C1 = "c1"
QUANTILE_COLS = ["pred"] + [f"{side}_{k}" for k in ["50", "80", "90", "95"] for side in ("lower", "upper")]
INTERVALS = ["50", "80", "90", "95"]


def code_to_uf(code):
    return B.UF_CODE[str(int(code))]


def load_truth():
    state = pd.read_csv(f"{EXT}/dengue_state.csv.gz", parse_dates=["date"])
    state["unit"] = state["adm_1"].map(code_to_uf)
    city = pd.read_csv(f"{EXT}/dengue_city.csv.gz", parse_dates=["date"])
    city["unit"] = city["adm_2"].astype(str)
    return {"state": state[state["unit"] != B.EXCLUDE_UF][["unit", "date", "casos"]], "city": city[["unit", "date", "casos"]]}


def params_paths(year):
    tag = C.SEASON_TAGS[year]
    seeds = {f"tft_v3_s{s}": f"{V.PARAMS_DIR}/params_{tag}_s{s}_full.parquet" for s in SEEDS}
    return seeds | {"tft_v2": f"{B.PARAMS_DIR}/params_{tag}.parquet",
            "b3": f"{B.PARAMS_DIR}/params_b3_{year}.parquet",
            "tft_v3": f"{V.PARAMS_DIR}/params_{tag}_full.parquet",
            "tft_v3_best": f"{V.PARAMS_DIR}/params_{tag}_best.parquet",
            "b3_v3": f"{V.PARAMS_DIR}/params_b3_{year}.parquet",
            "v3total_b3forma": f"{V.PARAMS_DIR}/params_hibrido_{year}.parquet",
            "tft_v4": f"outputs/params/v4/params_{tag}_full.parquet",
            "tft_v4_best": f"outputs/params/v4/params_{tag}_best.parquet"}


def read_rows(path):
    df = pd.read_parquet(path)
    df["geocode"] = df["geocode"].astype(str)
    df = df.sort_values(["geocode", "q"])
    return {gc: {p: g[p].to_numpy(float) for p in S.PARAMS} for gc, g in df.groupby("geocode")}


def ensure_derived(year, targets):
    """B3 com os alvos v3 e o híbrido exploratório (total do v3 + forma do B3)."""
    os.makedirs(V.PARAMS_DIR, exist_ok=True)
    p = params_paths(year)
    if not os.path.exists(p["b3_v3"]):
        R.b3_params(year, targets).to_parquet(p["b3_v3"], index=False)
    if os.path.exists(p["tft_v3"]) and not os.path.exists(p["v3total_b3forma"]):
        tft = pd.read_parquet(p["tft_v3"]).astype({"geocode": str}).sort_values(["geocode", "q"]).reset_index(drop=True)
        b3 = pd.read_parquet(p["b3_v3"]).astype({"geocode": str}).sort_values(["geocode", "q"]).reset_index(drop=True)
        assert (tft["geocode"].to_numpy() == b3["geocode"].to_numpy()).all()
        b3["total_cases"] = tft["total_cases"].to_numpy()
        b3.to_parquet(p["v3total_b3forma"], index=False)


def write_frames(years):
    os.makedirs(f"{OUT}/frames", exist_ok=True)
    targets = pd.read_parquet(V.TARGETS_PATH)
    for year in years:
        ensure_derived(year, targets)
        for model, path in params_paths(year).items():
            if not os.path.exists(path):
                continue
            todo_city = f"{OUT}/frames/{model}_{year}_city_None.parquet"
            todo_rho = [r for r in RHOS if not os.path.exists(f"{OUT}/frames/{model}_{year}_state_{r}.parquet")]
            if os.path.exists(todo_city) and not todo_rho:
                continue
            rows = read_rows(path)
            if not os.path.exists(todo_city):
                f = B.city_frames(rows, year)
                pd.concat([d.assign(unit=u) for u, d in f.items()], ignore_index=True).to_parquet(todo_city, index=False)
            for rho in todo_rho:
                f = B.state_frames(rows, year, rho)
                pd.concat([d.assign(unit=u) for u, d in f.items()], ignore_index=True).to_parquet(
                    f"{OUT}/frames/{model}_{year}_state_{rho}.parquet", index=False)
            print(f"{model} {year} ok", flush=True)
        write_c1(year)


def write_c1(year):
    """C1: média, semana a semana, de cada quantil das 5 sementes (só com todas presentes)."""
    for level, rho in [("city", None)] + [("state", r) for r in RHOS]:
        paths = [f"{OUT}/frames/{m}_{year}_{level}_{rho}.parquet" for m in SEED_MODELS]
        out = f"{OUT}/frames/{C1}_{year}_{level}_{rho}.parquet"
        if os.path.exists(out) or not all(os.path.exists(p) for p in paths):
            continue
        frames = [pd.read_parquet(p).sort_values(["unit", "date"]).reset_index(drop=True) for p in paths]
        for f in frames[1:]:
            assert (f[["unit", "date"]].to_numpy() == frames[0][["unit", "date"]].to_numpy()).all()
        avg = frames[0].copy()
        avg[QUANTILE_COLS] = np.mean([f[QUANTILE_COLS].to_numpy() for f in frames], axis=0)
        avg.to_parquet(out, index=False)
    print(f"{C1} {year} ok", flush=True)


def score(df, truth):
    df = df.assign(date=pd.to_datetime(df["date"]))
    s = R.score_frame(df, truth)
    w = df.merge(truth[["unit", "date"]], on=["unit", "date"])[["unit", "date"]].copy()
    for k in INTERVALS:
        w[f"width{k}"] = df.merge(truth[["unit", "date"]], on=["unit", "date"]).eval(f"upper_{k} - lower_{k}").to_numpy()
    return s.merge(w, on=["unit", "date"])


def own_scores(truth):
    rows = []
    for path in sorted(glob.glob(f"{OUT}/frames/*.parquet")):
        model, year, level, rho = os.path.basename(path)[:-8].rsplit("_", 3)
        s = score(pd.read_parquet(path), truth[level])
        rows.append(s.assign(model=model, cut_year=int(year), level=level, rho=None if rho == "None" else float(rho)))
    for path in sorted(glob.glob(f"{R.OUT}/direct/*.parquet")):
        model, year, level = os.path.basename(path)[:-8].split("_")
        s = score(pd.read_parquet(path), truth[level])
        rows.append(s.assign(model=model, cut_year=int(year), level=level, rho=None))
    return pd.concat(rows, ignore_index=True)


def select_rho(sc):
    """rho por modelo e corte, só com cortes <= Y-2; retorna também o rho do corte final (Y = 2026)."""
    st = sc[(sc["level"] == "state") & sc["rho"].notna()]
    per = st.groupby(["model", "cut_year", "rho", "unit"], as_index=False)["wis"].mean()
    per["lw"] = np.log(per["wis"] + 1)
    per = per.groupby(["model", "cut_year", "rho"], as_index=False)["lw"].mean()
    out = {}
    for model, g in per.groupby("model"):
        for y in YEARS + [2026]:
            prior = g[g["cut_year"] <= y - 2].groupby("rho")["lw"].mean()
            out[(model, y)] = float(prior.idxmin()) if len(prior) else DEFAULT_RHO
    return out


def apply_rho(sc, chosen):
    keep = sc["rho"].isna() | np.array([r == chosen.get((m, y)) for m, y, r in zip(sc["model"], sc["cut_year"], sc["rho"])])
    return sc[keep]


def official_scores(truth):
    out = []
    for level in ["state", "city"]:
        d = pd.read_csv(f"{EXT}/predictions_all_models_dengue_{level}.csv.gz", index_col=0, parse_dates=["date"])
        d = d.drop(columns=["wis"], errors="ignore")
        d["unit"] = d["adm_1"].map(code_to_uf) if level == "state" else d["adm_2"].astype(str)
        d = d[d["unit"] != B.EXCLUDE_UF].drop_duplicates(["model", "validation", "unit", "date"])
        for (model, val), g in d.groupby(["model", "validation"]):
            s = score(g, truth[level])
            out.append(s.assign(model=model, cut_year=OFFICIAL_YEARS[int(val)], level=level, rho=None))
    return pd.concat(out, ignore_index=True)


def ratio_table(all_sc, level, focus):
    base = BASELINE[level]
    sub = all_sc[(all_sc["level"] == level) & (all_sc["cut_year"].isin(OFFICIAL_YEARS.values()))]
    # todas as semanas pontuadas por cada modelo; a média da unidade-temporada é a usada pelo desafio
    per = sub.groupby(["model", "unit", "cut_year"], as_index=False)["wis"].mean()
    b = per[per["model"] == base].rename(columns={"wis": "b"})[["unit", "cut_year", "b"]]
    m = per.merge(b, on=["unit", "cut_year"])
    m["lr"] = np.log(m["wis"].clip(lower=1e-9) / m["b"].clip(lower=1e-9))
    per_unit = m.groupby(["model", "unit"])["lr"].mean().unstack("unit")
    tab = pd.DataFrame({"R": np.exp(m.groupby("model")["lr"].mean()), "pares": m.groupby("model").size(),
                        "unidades_melhor_que_baseline": (per_unit < 0).sum(axis=1), "unidades": per_unit.notna().sum(axis=1)})
    for y in OFFICIAL_YEARS.values():
        tab[f"R_{y}"] = np.exp(m[m["cut_year"] == y].groupby("model")["lr"].mean())
    tab = tab.sort_values("R")
    complete = tab[tab["pares"] == tab["pares"].max()]
    ranks = complete[~complete.index.isin([x for x in focus if x not in [base, SUBMITTED_V1]])]
    return tab, ranks.index.tolist()


def intervals_table(all_sc, level, models):
    sub = all_sc[(all_sc["level"] == level) & (all_sc["cut_year"].isin(OFFICIAL_YEARS.values())) & all_sc["model"].isin(models)]
    cols = [f"cov{k}" for k in INTERVALS] + [f"width{k}" for k in INTERVALS] + ["wis", "dispersion", "under", "over"]
    t = sub.groupby("model")[cols].mean()
    t[[f"cov{k}" for k in INTERVALS]] *= 100
    return t.reindex([m for m in models if m in t.index])


def forecast_table(chosen):
    rows = []
    for level, unit_col in [("state", "adm_1"), ("city", "adm_2")]:
        d = pd.read_csv(f"{EXT}/forecast_all_models_dengue_{level}.csv.gz", index_col=0, parse_dates=["date"])
        d["unit"] = d[unit_col].map(code_to_uf) if level == "state" else d[unit_col].astype(str)
        d = d[(d["unit"] != B.EXCLUDE_UF) & d["model"].isin([BASELINE[level], SUBMITTED_V1])]
        rows.append(d.assign(level=level)[["model", "level", "unit", "date", "pred", "lower_90", "upper_90"]])
        path = os.path.join(SUBS, f"dengue_{level}", "final_2026", "_todos_estados.csv" if level == "state" else "_todas_cidades.csv")
        if os.path.exists(path):
            v = pd.read_csv(path, parse_dates=["date"]).rename(columns={"uf": "unit", "geocode": "unit"})
            v["unit"] = v["unit"].astype(str)
            rows.append(v.assign(model=PRIMARY, level=level)[["model", "level", "unit", "date", "pred", "lower_90", "upper_90"]])
    a = pd.concat(rows, ignore_index=True)
    a["i_peak"] = a.groupby(["model", "level", "unit"])["pred"].transform("idxmax")
    peak = a.loc[a["i_peak"].unique(), ["model", "level", "unit", "date", "pred", "lower_90", "upper_90"]].rename(columns={
        "date": "pico", "pred": "pico_casos", "lower_90": "pico_lower90", "upper_90": "pico_upper90"})
    tot = a.groupby(["model", "level", "unit"], as_index=False)["pred"].sum().rename(columns={"pred": "soma_medianas"})
    return tot.merge(peak, on=["model", "level", "unit"])


def write_final(chosen):
    """previsão final 2026-27 do v3 (não enviada), validada com as mesmas regras do desafio."""
    path = f"{V.PARAMS_DIR}/params_final_full.parquet"
    if not os.path.exists(path):
        return None
    rho = chosen.get((PRIMARY, 2026), DEFAULT_RHO)
    rows = read_rows(path)
    assert len(rows) == B.N_MUNICIPIOS
    for kind, frames, key, name in [("dengue_city", B.city_frames(rows, 2026), "geocode", "_todas_cidades.csv"),
                                    ("dengue_state", B.state_frames(rows, 2026, rho), "uf", "_todos_estados.csv")]:
        d = os.path.join(SUBS, kind, "final_2026")
        os.makedirs(d, exist_ok=True)
        tidy = []
        for unit, df in frames.items():
            ok, errs = S.validate(df, 2026, verbose=False)
            assert ok, f"{kind} {unit}: {errs}"
            df.to_csv(os.path.join(d, f"{unit}.csv"), index=False)
            tidy.append(df.assign(**{key: unit}))
        pd.concat(tidy).to_csv(os.path.join(d, name), index=False)
    return rho


def rolling_table(sel):
    prim = sel[sel["cut_year"].isin(range(2015, 2025))]
    out = []
    for ref in ["b3", "b3_v3"]:
        if ref in prim["model"].values:
            out.append(R.relative_table(prim, ref=ref).assign(referencia=ref))
    return pd.concat(out, ignore_index=True)


def seed_table(sel, level="state", ref="b3"):
    """Protocolo, seção 3: WIS relativo por temporada de cada semente, do C1 e o desvio entre sementes.

    Mesma conta de R.relative_table: razão de (WIS + 1) por unidade-temporada, média geométrica na temporada.
    A linha "todas" é a média geométrica das temporadas, que é a métrica primária.
    """
    prim = sel[(sel["level"] == level) & sel["cut_year"].isin(range(2015, 2025))]
    per = prim.groupby(["model", "cut_year", "unit"], as_index=False)["wis"].mean()
    wide = per.pivot_table(index=["cut_year", "unit"], columns="model", values="wis")
    cols = [m for m in [C1] + SEED_MODELS + [PRIMARY] if m in wide.columns]
    lr = (np.log(wide[cols] + 1)).sub(np.log(wide[ref] + 1), axis=0).dropna()
    by = lr.groupby("cut_year").mean()
    by.loc["todas"] = by.mean()
    tab = np.exp(by)
    seeds = [m for m in SEED_MODELS if m in tab.columns]
    tab["dp_sementes"] = tab[seeds].std(axis=1, ddof=1)
    tab["amplitude_sementes"] = tab[seeds].max(axis=1) - tab[seeds].min(axis=1)
    return tab.rename(columns={PRIMARY: "tft_v3_s42_rtx3050"})


def report():
    os.makedirs(REPORT, exist_ok=True)
    pd.set_option("display.width", 220, "display.max_columns", 30, "display.max_rows", 80)
    truth = load_truth()
    sc = own_scores(truth)
    chosen = select_rho(sc)
    sel = apply_rho(sc, chosen)
    off = official_scores(truth)
    # os modelos oficiais têm prefixo próprio: não colidem com os nossos
    all_sc = pd.concat([sel, off], ignore_index=True)
    ours = [C1] + SEED_MODELS + ["tft_v4", "tft_v4_best", "tft_v3", "tft_v3_best", "v3total_b3forma", "tft_v2", "b3", "b3_v3", "b1", "b2"]
    pd.Series({f"{m}|{y}": r for (m, y), r in chosen.items()}, name="rho").to_csv(f"{REPORT}/rho_by_cut.csv")
    rho_final = write_final(chosen)
    print("rho do corte final:", rho_final)
    for level in ["state", "city"]:
        tab, _ = ratio_table(all_sc, level, ours)
        tab.to_csv(f"{REPORT}/official_ratio_{level}.csv")
        print(f"\nRazão oficial contra {BASELINE[level]} ({level})\n", tab.round(3).to_string())
        show = [BASELINE[level], SUBMITTED_V1] + ours + (["3rd_imdc_emap_lstm"] if level == "state" else [])
        iv = intervals_table(all_sc, level, show)
        iv.to_csv(f"{REPORT}/intervals_{level}.csv")
        print(f"\nIntervalos, 4 validações ({level})\n", iv.round(1).to_string())
        by = all_sc[(all_sc["level"] == level) & all_sc["cut_year"].isin(OFFICIAL_YEARS.values()) & all_sc["model"].isin(show)]
        byv = by.groupby(["model", "cut_year"])[[f"cov{k}" for k in INTERVALS] + ["wis"]].mean()
        byv[[f"cov{k}" for k in INTERVALS]] *= 100
        byv.to_csv(f"{REPORT}/intervals_by_validation_{level}.csv")
    rol = rolling_table(sel)
    rol.to_csv(f"{REPORT}/rolling_relative.csv", index=False)
    print("\nOrigem móvel, 2015/16 a 2024/25\n", rol.round(3).to_string(index=False))
    seeds = seed_table(sel)
    seeds.to_csv(f"{REPORT}/sementes_por_temporada.csv")
    print("\nWIS relativo ao B3 por temporada e semente (UFs)\n", seeds.round(3).to_string())
    fc = forecast_table(chosen)
    fc.to_csv(f"{REPORT}/forecast_2026_27.csv", index=False)
    print("\nPrevisão 2026-27: soma das medianas\n", fc.groupby(["level", "model"])["soma_medianas"].sum().round(0).to_string())


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "frames":
        write_frames([int(y) for y in sys.argv[2:]] or YEARS)
    else:
        report()
