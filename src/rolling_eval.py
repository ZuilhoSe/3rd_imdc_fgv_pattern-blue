"""
IMDC 2026 — AVALIAÇÃO COM ORIGEM MÓVEL (Fase 1 do artigo).

Compara o TFT com três baselines nas temporadas 2015/16 a 2024/25, usando em cada corte
(EW25/Y) somente informação disponível até ele:

  B1 persistência : últimas 52 semanas observadas, alinhadas por semana da temporada, com
                    erro multiplicativo empírico (razão entre totais de temporadas seguidas,
                    agrupada por nível).
  B2 climatologia : quantis históricos de casos por semana da temporada, janela de +-2 semanas.
  B3 climatologia de parâmetros : quantis históricos de total/alpha/beta/pico de cada município,
                    com a MESMA reconstrução e agregação do TFT. É a ablação central.

Protocolo, definido antes de olhar os resultados (docs/evaluation_protocol.md):
  * métrica primária: WIS relativo ao B3 no nível estadual (média geométrica por UF-temporada);
  * rho de cada corte Y escolhido só com temporadas já encerradas em Y (cortes <= Y-2);
  * 2025/26 é parcial (dados até EW25/2026): reportada à parte, fora da análise primária.

Uso (a partir de src/):
  python rolling_eval.py baselines          # params do B3 + previsões B1/B2
  python rolling_eval.py score              # pontua o que houver (incremental)
  python rolling_eval.py report             # tabelas em ../reports/rolling/
"""
import glob
import os
import re
import sys
import numpy as np
import pandas as pd

import build_submissions as B
import common as C
import imdc_submission as S
from preprocess import season_start

OUT = "outputs/rolling"
REPORT = "../reports/rolling"
CUT_YEARS = list(range(2015, 2026))
PRIMARY = list(range(2015, 2025))      # 2025/26 só tem dados até EW25/2026
RHOS = [0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 0.9, 1.0]
DEFAULT_RHO = 0.5                      # cortes sem temporada encerrada anterior para calibrar
ALPHAS = {"50": 0.5, "80": 0.2, "90": 0.1, "95": 0.05}
LEVELS = np.array([S.QLEVELS[c] for c in S.INTERVAL_ORDER])
PARAM_MODELS = {"b3": "params_b3_{y}.parquet"}


# ------------------------------------------------------------------ verdade
def load_truth():
    b = pd.read_parquet(C.BASE_PATH, columns=["geocode", "date", "casos", "uf", "season"])
    b["geocode"] = b["geocode"].astype(str)
    city = b[b["geocode"].isin(B.DENGUE_CITIES)].rename(columns={"geocode": "unit"})[["unit", "date", "casos", "season"]]
    state = (b[b["uf"] != B.EXCLUDE_UF].groupby(["uf", "date", "season"], as_index=False)["casos"].sum()
             .rename(columns={"uf": "unit"}))
    out = {}
    for level, df in [("city", city), ("state", state)]:
        df = df.copy()
        starts = {s: season_start(s) for s in df["season"].unique()}
        df["idx"] = (df["date"] - df["season"].map(starts)).dt.days // 7
        out[level] = df.sort_values(["unit", "date"]).reset_index(drop=True)
    return out


# ------------------------------------------------------------------ baselines diretas
def b1_frames(df, year):
    """persistência das últimas 52 semanas, com erro multiplicativo empírico."""
    W = len(S.season_weeks(year))
    cd = C.cut_date(year)
    totals = df[(df["season"] >= 2011) & (df["season"] <= year - 1)].groupby(["unit", "season"])["casos"].sum()
    logt = np.log1p(totals).unstack("season")
    ratios = logt.diff(axis=1).to_numpy().ravel()
    ratios = ratios[~np.isnan(ratios)]
    q = np.quantile(ratios, LEVELS)[:, None]
    frames = {}
    for unit, g in df.groupby("unit"):
        prev = g[g["season"] == year - 1].set_index("idx")["casos"]
        cur = g[(g["season"] == year) & (g["date"] <= cd)].set_index("idx")["casos"]
        ref = prev.reindex(range(W)).ffill().bfill()
        ref.loc[cur.index.intersection(ref.index)] = cur
        mat = (ref.to_numpy(float)[None, :] + 1) * np.exp(q) - 1
        frames[unit] = S.build_df(year, mat)
    return frames


def b2_frames(df, year, half_window=2):
    """climatologia: quantis por semana da temporada, com tudo o que foi observado até o corte."""
    W = len(S.season_weeks(year))
    past = df[df["date"] <= C.cut_date(year)]
    frames = {}
    for unit, g in past.groupby("unit"):
        idx, y = g["idx"].to_numpy(), g["casos"].to_numpy(float)
        mat = np.column_stack([np.quantile(y[np.abs(idx - i) <= half_window], LEVELS) for i in range(W)])
        frames[unit] = S.build_df(year, mat)
    return frames


def b3_params(year, targets):
    """quantis históricos dos descritores de cada município (temporadas encerradas até o corte)."""
    t = C.season_targets_for_cut(year, targets)
    t["total_cases"] = t["obs_total"] if "obs_total" in t else np.expm1(t["log_total_cases"])
    rows = []
    for gc, g in t.groupby("geocode"):
        q = {p: np.quantile(g[p].to_numpy(float), C.QUANTILE_LEVELS) for p in S.PARAMS}
        rows.append(pd.DataFrame({"geocode": gc, "q": C.QUANTILE_LEVELS, **q}))
    return pd.concat(rows, ignore_index=True)


def write_baselines():
    os.makedirs(f"{OUT}/direct", exist_ok=True)
    targets = pd.read_parquet(C.TARGETS_PATH)
    truth = load_truth()
    for year in CUT_YEARS:
        path = os.path.join(B.PARAMS_DIR, f"params_b3_{year}.parquet")
        if not os.path.exists(path):
            b3_params(year, targets).to_parquet(path, index=False)
        for level, df in truth.items():
            for name, fn in [("b1", b1_frames), ("b2", b2_frames)]:
                frames = fn(df, year)
                allf = pd.concat([f.assign(unit=u) for u, f in frames.items()], ignore_index=True)
                allf.to_parquet(f"{OUT}/direct/{name}_{year}_{level}.parquet", index=False)
        print(f"baselines {year} ok", flush=True)


# ------------------------------------------------------------------ pontuação
def score_frame(df, truth):
    """df: colunas de submissão + unit; retorna por semana WIS e componentes (Bracher et al. 2021)."""
    m = df.assign(date=pd.to_datetime(df["date"])).merge(truth[["unit", "date", "casos"]], on=["unit", "date"])
    y, med = m["casos"].to_numpy(float), m["pred"].to_numpy(float)
    K = len(ALPHAS) + 0.5
    disp, under, over = np.zeros(len(m)), np.zeros(len(m)), np.zeros(len(m))
    for k, a in ALPHAS.items():
        lo, hi = m[f"lower_{k}"].to_numpy(float), m[f"upper_{k}"].to_numpy(float)
        disp += a / 2 * (hi - lo)
        over += np.maximum(lo - y, 0)     # previsão acima do observado
        under += np.maximum(y - hi, 0)    # previsão abaixo do observado
        m[f"cov{k}"] = (y >= lo) & (y <= hi)
    ae = np.abs(y - med)
    over += 0.5 * np.maximum(med - y, 0)
    under += 0.5 * np.maximum(y - med, 0)
    m["ae"], m["dispersion"], m["under"], m["over"] = ae, disp / K, under / K, over / K
    m["wis"] = m["dispersion"] + m["under"] + m["over"]
    keep = ["unit", "date", "casos", "pred", "wis", "dispersion", "under", "over", "ae"] + [f"cov{k}" for k in ALPHAS]
    return m[keep]


def _save(score, model, year, level, rho):
    score.assign(model=model, cut_year=year, level=level, rho=rho).to_parquet(
        f"{OUT}/scores/{model}_{year}_{level}_{rho}.parquet", index=False)


def score_param_model(model, params_path, year, truth):
    """TFT ou B3: cidades diretas; UFs por soma dos municípios em cada rho da grade."""
    missing = [r for r in RHOS if not os.path.exists(f"{OUT}/scores/{model}_{year}_state_{r}.parquet")]
    if not missing and os.path.exists(f"{OUT}/scores/{model}_{year}_city_None.parquet"):
        return
    df = pd.read_parquet(params_path)
    df["geocode"] = df["geocode"].astype(str)
    df = df.sort_values(["geocode", "q"])
    rows = {gc: {p: g[p].to_numpy(float) for p in S.PARAMS} for gc, g in df.groupby("geocode")}
    city = pd.concat([f.assign(unit=u) for u, f in B.city_frames(rows, year).items()], ignore_index=True)
    _save(score_frame(city, truth["city"]), model, year, "city", None)
    for rho in missing:
        st = pd.concat([f.assign(unit=u) for u, f in B.state_frames(rows, year, rho).items()], ignore_index=True)
        _save(score_frame(st, truth["state"]), model, year, "state", rho)
    print(f"{model} {year} ok", flush=True)


def score_all():
    os.makedirs(f"{OUT}/scores", exist_ok=True)
    truth = load_truth()
    for path in sorted(glob.glob(f"{OUT}/direct/*.parquet")):
        model, year, level = os.path.basename(path)[:-8].split("_")
        _save(score_frame(pd.read_parquet(path), truth[level]), model, int(year), level, None)
    for year in CUT_YEARS:
        score_param_model("b3", os.path.join(B.PARAMS_DIR, f"params_b3_{year}.parquet"), year, truth)
        tag = C.SEASON_TAGS[year]
        for path in sorted(glob.glob(os.path.join(B.PARAMS_DIR, f"params_{tag}*.parquet"))):
            t = os.path.basename(path)[len("params_"):-len(".parquet")]
            if re.fullmatch(rf"{tag}(_s\d+)?", t):   # ignora params_test1_2022 (modelo antigo)
                score_param_model(f"tft-s{C.tag_seed(t)}", path, year, truth)


# ------------------------------------------------------------------ relatório
def select_rho(scores):
    """rho por modelo e corte, só com cortes <= Y-2 (temporadas já encerradas no corte Y)."""
    st = scores[(scores["level"] == "state") & scores["rho"].notna()]
    per = st.groupby(["model", "cut_year", "rho", "unit"], as_index=False)["wis"].mean()
    per["lw"] = np.log(per["wis"] + 1)
    per = per.groupby(["model", "cut_year", "rho"], as_index=False)["lw"].mean()
    out = {}
    for model, g in per.groupby("model"):
        for year in CUT_YEARS:
            prior = g[g["cut_year"] <= year - 2].groupby("rho")["lw"].mean()
            out[(model, year)] = prior.idxmin() if len(prior) else DEFAULT_RHO
    return out


def load_selected():
    scores = pd.concat([pd.read_parquet(p) for p in glob.glob(f"{OUT}/scores/*.parquet")], ignore_index=True)
    chosen = select_rho(scores)
    keep = scores["rho"].isna() | [
        r == chosen.get((m, y)) for m, y, r in zip(scores["model"], scores["cut_year"], scores["rho"])]
    return scores[keep], chosen


def relative_table(sel, ref="b3", n_boot=2000, seed=0):
    """WIS relativo ao ref: média geométrica por unidade-temporada; IC por bootstrap de temporadas."""
    per = sel.groupby(["level", "model", "cut_year", "unit"], as_index=False)["wis"].mean()
    rng = np.random.default_rng(seed)
    rows = []
    for level, g in per.groupby("level"):
        wide = g.pivot_table(index=["cut_year", "unit"], columns="model", values="wis")
        for model in wide.columns:
            lr = (np.log(wide[model] + 1) - np.log(wide[ref] + 1)).dropna()
            by = lr.groupby("cut_year").mean()
            boots = rng.choice(by.to_numpy(), size=(n_boot, len(by))).mean(axis=1)
            rows.append({"nivel": level, "modelo": model, "wis_rel": np.exp(by.mean()),
                         "ic95_inf": np.exp(np.quantile(boots, 0.025)), "ic95_sup": np.exp(np.quantile(boots, 0.975)),
                         "melhor_que_ref_%": 100 * (lr < 0).mean(), "temporadas": len(by)})
    return pd.DataFrame(rows)


def report():
    os.makedirs(REPORT, exist_ok=True)
    sel, chosen = load_selected()
    prim = sel[sel["cut_year"].isin(PRIMARY)]
    fmt = lambda v: f"{v:,.3f}"
    rel = relative_table(prim)
    rel.to_csv(f"{REPORT}/relative_wis.csv", index=False)
    print("\nWIS relativo ao B3 (primária: nivel=state)\n", rel.to_string(index=False, float_format=fmt))

    per = prim.groupby(["level", "model", "cut_year", "unit"], as_index=False)["wis"].mean()
    season = per.pivot_table(index=["level", "cut_year"], columns="model", values="wis", aggfunc="median")
    season.to_csv(f"{REPORT}/median_wis_by_season.csv")
    print("\nWIS mediano por temporada\n", season.round(1).to_string())

    comp = prim.groupby(["level", "model"])[["wis", "dispersion", "under", "over", "cov50", "cov80", "cov90", "cov95"]].mean()
    comp.to_csv(f"{REPORT}/components_coverage.csv")
    print("\nComponentes (média semanal) e cobertura\n", comp.round(3).to_string())

    pd.Series({f"{m}|{y}": r for (m, y), r in chosen.items()}, name="rho").to_csv(f"{REPORT}/rho_by_cut.csv")
    partial = sel[sel["cut_year"] == 2025]
    if len(partial):
        p = partial.groupby(["level", "model", "unit"], as_index=False)["wis"].mean().pivot_table(
            index="level", columns="model", values="wis", aggfunc="median")
        print("\n2025/26 (parcial, fora da primária) — WIS mediano\n", p.round(1).to_string())


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    {"baselines": write_baselines, "score": score_all, "report": report}[cmd]()
