"""
IMDC 2026 — análise para a apresentação (5 min).

Avalia as validações no TOTAL DA TEMPORADA (a série semanal observada não está no
repositório; season_targets.parquet traz o total observado por município/temporada):
  test1 (corte EW25/2022) -> temporada 2022-23 (season=2023)
  test2 (corte EW25/2023) -> 2023-24
  test3 (corte EW25/2024) -> 2024-25
  test4 (corte EW25/2025) -> 2025-26 ainda incompleta nos dados -> fora
Baselines ingênuos: total da última temporada e mediana das 3 últimas.

Estados: total estadual por Monte Carlo com a mesma cópula gaussiana das submissões
(rho de outputs/state_rho.json), somando todos os municípios da UF (ES excluído).

Saídas: presentation/figures/*.png e presentation/results/*.csv
Uso (da raiz do repo): python presentation/analysis.py
"""
import json
import os

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LogNorm, TwoSlopeNorm, LinearSegmentedColormap
from scipy.stats import norm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
FIG, RES = P("presentation", "figures"), P("presentation", "results")
os.makedirs(FIG, exist_ok=True)
os.makedirs(RES, exist_ok=True)

TESTS = {"test1": 2023, "test2": 2024, "test3": 2025}   # tag -> season (ano final)
QS = np.array([0.02, 0.10, 0.25, 0.50, 0.75, 0.90, 0.98])
RHO = json.load(open(P("src", "outputs", "state_rho.json")))["rho"]
MIN_POP_RANK = 100_000   # ranking de cidades só com municípios >= 100 mil hab.
MIN_OBS_RANK = 200       # ... e com média >= 200 casos/temporada (epidemias de fato)

# paleta (dataviz reference palette)
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, RED, GRAY_MID = "#2a78d6", "#eb6834", "#e34948", "#f0efec"
SEQ = LinearSegmentedColormap.from_list("seq", ["#fdeee6", "#f6b894", "#eb6834", "#b8431a", "#6e2208"])
DIV = LinearSegmentedColormap.from_list("div", ["#104281", "#3987e5", "#b7d3f6", GRAY_MID,
                                                "#f5b3b2", "#e34948", "#8f1f1e"])
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": GRID,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150})

UF_CODE = {"11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
           "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
           "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR",
           "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF"}


# ------------------------------------------------------------------ dados
def load_params(tag):
    df = pd.read_parquet(P("src", "outputs", "params", f"params_{tag}.parquet"))
    df["geocode"] = df["geocode"].astype(str)
    return df.sort_values(["geocode", "q"])


def total_quantiles(tag):
    """quantis do total previsto por município (colunas q02..q98)."""
    w = load_params(tag).pivot(index="geocode", columns="q", values="total_cases")
    w = pd.DataFrame(np.sort(w.to_numpy(), axis=1), index=w.index,
                     columns=[f"q{int(round(q * 100)):02d}" for q in QS])
    pk = load_params(tag).query("q == 0.5").set_index("geocode")["peak_week"]
    return w.assign(peak_pred=pk)


tg = pd.read_parquet(P("data", "processed", "season_targets.parquet"))
tg["geocode"] = tg["geocode"].astype(str)
names = pd.read_csv(P("data", "processed", "static_features_tft.csv"), dtype={"geocode": str})
names = names.set_index("geocode")[["geocode_name", "uf"]]
pop = pd.read_csv(P("presentation", "data", "municipios_pop.csv"), dtype={"ibge": str})
pop = pop.set_index("ibge")["pop2021"]


# ------------------------------------------------ avaliação por município
rows = []
for tag, season in TESTS.items():
    q = total_quantiles(tag)
    obs = tg[tg["season"] == season].set_index("geocode")
    hist = tg[tg["season"] < season].pivot(index="geocode", columns="season", values="obs_total")
    d = q.join(obs[["obs_total", "peak_idx", "has_fit"]], how="inner")
    d["base_last"] = hist[season - 1].reindex(d.index)
    d["base_med3"] = hist[[season - 3, season - 2, season - 1]].median(axis=1).reindex(d.index)
    d["tag"], d["season"] = tag, f"{season - 1}-{str(season)[2:]}"
    rows.append(d.reset_index())
city = pd.concat(rows, ignore_index=True)
city["uf"] = city["geocode"].str[:2].map(UF_CODE)
city["name"] = city["geocode"].map(names["geocode_name"])
city["pop"] = city["geocode"].map(pop)

le = lambda pred, obs: np.log((pred + 1) / (obs + 1))   # erro log do total
city["log_err"] = le(city["q50"], city["obs_total"])
city["log_err_last"] = le(city["base_last"], city["obs_total"])
city["log_err_med3"] = le(city["base_med3"], city["obs_total"])
city["in80"] = city["obs_total"].between(city["q10"], city["q90"])
city["in96"] = city["obs_total"].between(city["q02"], city["q98"])
city["peak_err"] = np.where(city["has_fit"], (city["peak_pred"] - city["peak_idx"]).abs(), np.nan)
city.to_csv(os.path.join(RES, "city_season_eval.csv"), index=False)


def summarize(d):
    return pd.Series({
        "fator_erro_mediano": np.exp(d["log_err"].abs().median()),
        "fator_erro_ult_temp": np.exp(d["log_err_last"].abs().median()),
        "fator_erro_med3": np.exp(d["log_err_med3"].abs().median()),
        "cobertura_80": d["in80"].mean(), "cobertura_96": d["in96"].mean(),
        "erro_pico_sem": d["peak_err"].median(), "n": len(d)})


summ_all = city.groupby("season").apply(summarize)
big = city[(city["pop"] >= MIN_POP_RANK) & (city["uf"] != "ES")]   # ES fica fora do desafio
summ_big = big.groupby("season").apply(summarize)


# ------------------------------------------------------- ranking de cidades
def rank_units(d, key, extra):
    g = d.groupby(key).agg(abs_log_err=("log_err", lambda s: s.abs().mean()),
                           vies=("log_err", "mean"), cob80=("in80", "mean"),
                           erro_pico=("peak_err", "mean"), obs_medio=("obs_total", "mean"),
                           prev_medio=("q50", "mean"), n=("log_err", "size"), **extra)
    g["fator_erro"] = np.exp(g["abs_log_err"])
    return g.sort_values("abs_log_err")


crank = rank_units(big, "geocode", {"name": ("name", "first"), "uf": ("uf", "first"),
                                    "pop": ("pop", "first")})
crank = crank[(crank["n"] == len(TESTS)) & (crank["obs_medio"] >= MIN_OBS_RANK)]
crank.to_csv(os.path.join(RES, "ranking_cidades.csv"))


# ------------------------------------------------ estados (Monte Carlo + cópula)
def state_total_quantiles(tag, D=4000, seed=0):
    df = load_params(tag)
    df["uf"] = df["geocode"].str[:2].map(UF_CODE)
    out = {}
    rng = np.random.default_rng(seed)
    for uf, g in df[df["uf"] != "ES"].groupby("uf"):
        V = np.sort(g.pivot(index="geocode", columns="q", values="total_cases").to_numpy(), axis=1)
        M = V.shape[0]
        z = np.sqrt(RHO) * rng.standard_normal((1, D)) + np.sqrt(1 - RHO) * rng.standard_normal((M, D))
        u = norm.cdf(z)
        j = np.clip(np.searchsorted(QS, u, side="right") - 1, 0, len(QS) - 2)
        w = np.clip((u - QS[j]) / (QS[j + 1] - QS[j]), 0, 1)
        v0, v1 = np.take_along_axis(V, j, 1), np.take_along_axis(V, j + 1, 1)
        tot = (v0 + w * (v1 - v0)).sum(axis=0)
        out[uf] = np.quantile(tot, [0.025, 0.10, 0.5, 0.90, 0.975])
    return pd.DataFrame(out, index=["q025", "q10", "q50", "q90", "q975"]).T


srows = []
for tag, season in TESTS.items():
    s = state_total_quantiles(tag)
    o = city[city["tag"] == tag].groupby("uf")[["obs_total", "base_last", "base_med3"]].sum()
    s = s.join(o)
    s["tag"], s["season"] = tag, f"{season - 1}-{str(season)[2:]}"
    srows.append(s.reset_index(names="uf"))
state = pd.concat(srows, ignore_index=True)
state["log_err"] = le(state["q50"], state["obs_total"])
state["log_err_last"] = le(state["base_last"], state["obs_total"])
state["log_err_med3"] = le(state["base_med3"], state["obs_total"])
state["in80"] = state["obs_total"].between(state["q10"], state["q90"])
state["in95"] = state["obs_total"].between(state["q025"], state["q975"])
state.to_csv(os.path.join(RES, "state_season_eval.csv"), index=False)

srank = state.groupby("uf").agg(abs_log_err=("log_err", lambda s: s.abs().mean()),
                                vies=("log_err", "mean"), cob80=("in80", "mean"),
                                cob95=("in95", "mean"), obs_medio=("obs_total", "mean"),
                                prev_medio=("q50", "mean"))
srank["fator_erro"] = np.exp(srank["abs_log_err"])
srank = srank.sort_values("abs_log_err")
srank.to_csv(os.path.join(RES, "ranking_estados.csv"))

summ_state = state.groupby("season").apply(lambda d: pd.Series({
    "fator_erro_mediano": np.exp(d["log_err"].abs().median()),
    "fator_erro_ult_temp": np.exp(d["log_err_last"].abs().median()),
    "fator_erro_med3": np.exp(d["log_err_med3"].abs().median()),
    "cobertura_80": d["in80"].mean(), "cobertura_95": d["in95"].mean(),
    "brasil_obs": d["obs_total"].sum(), "brasil_prev": d["q50"].sum()}))


# ------------------------------------------------ previsão final 2026-27
fq = total_quantiles("final")
fq["uf"] = fq.index.str[:2].map(UF_CODE)
fq["pop"] = fq.index.map(pop)
fq["name"] = fq.index.map(names["geocode_name"])
fq["inc"] = fq["q50"] / fq["pop"] * 1e5
fs = state_total_quantiles("final")
uf_pop = fq.groupby("uf")["pop"].sum()
fs["pop"] = uf_pop
fs["inc"] = fs["q50"] / fs["pop"] * 1e5
fs["inc_lo"], fs["inc_hi"] = fs["q10"] / fs["pop"] * 1e5, fs["q90"] / fs["pop"] * 1e5
last = tg[tg["season"] == 2025].assign(uf=lambda d: d["geocode"].str[:2].map(UF_CODE))
fs["obs_2024_25"] = last.groupby("uf")["obs_total"].sum()
fs = fs.sort_values("inc", ascending=False)
fs.to_csv(os.path.join(RES, "previsao_estados_2026_27.csv"))
fq.sort_values("q50", ascending=False).to_csv(os.path.join(RES, "previsao_municipios_2026_27.csv"))

# temporada 2026-27 com a curva semanal nacional (soma das submissões estaduais)
sub_dir = P("src", "outputs", "submissions", "dengue_state", "final_2026", "_todos_estados.csv")
nat = pd.read_csv(sub_dir).groupby("date")[["pred", "lower_80", "upper_80", "lower_50", "upper_50"]].sum()


# ------------------------------------------------------------------ figuras
def save(fig, name):
    fig.savefig(os.path.join(FIG, name), bbox_inches="tight", facecolor="white")
    plt.close(fig)


ufs = gpd.read_file(P("presentation", "data", "brazil_states.geojson"))[["sigla", "geometry"]]
mun_path = P("presentation", "data", "municipios_simpl.geojson")
if not os.path.exists(mun_path):   # simplifica o geojson do IBGE (tbrugz/geodata-br) uma vez
    # fonte: https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-100-mun.json
    raw = gpd.read_file("https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-100-mun.json")
    raw["geometry"] = raw.to_crs(5880).simplify(1500).to_crs(4326)
    raw[["id", "geometry"]].to_file(mun_path, driver="GeoJSON")
mun = gpd.read_file(mun_path).rename(columns={"id": "geocode"})


# 1) mapa estadual: incidência prevista 2026-27
g = ufs.merge(fs.reset_index(names="sigla"), on="sigla", how="left")
fig, ax = plt.subplots(figsize=(7.5, 7.5))
g[g["inc"].isna()].plot(ax=ax, color="#dcdbd6", edgecolor="white", linewidth=0.8, hatch="///")
g.dropna(subset=["inc"]).plot(ax=ax, column="inc", cmap=SEQ, edgecolor="white", linewidth=0.8,
                              legend=True, norm=LogNorm(vmin=max(g["inc"].min(), 10), vmax=g["inc"].max()),
                              legend_kwds={"label": "casos previstos / 100 mil hab. (mediana)",
                                           "shrink": 0.55, "orientation": "horizontal", "pad": 0.02})
OFFSHORE = {"RN": (-31.5, -4.8), "PB": (-31.5, -7.0), "PE": (-31.5, -9.2), "AL": (-31.5, -11.4),
            "SE": (-31.5, -13.6), "DF": (-36.8, -17.0), "ES": (-36.8, -20.0), "RJ": (-40.5, -24.6)}
for _, r in g.iterrows():
    c = r.geometry.representative_point()
    lab = r["sigla"] if pd.isna(r["inc"]) else f"{r['sigla']} {r['inc']:,.0f}".replace(",", ".")
    if r["sigla"] in OFFSHORE:   # UFs pequenas: rótulo fora, com linha guia
        ax.annotate(lab, (c.x, c.y), xytext=OFFSHORE[r["sigla"]], ha="left", va="center",
                    fontsize=7.5, color=INK, arrowprops={"arrowstyle": "-", "color": INK2, "lw": 0.6})
        continue
    lab = lab.replace(" ", "\n")
    ax.annotate(lab, (c.x, c.y), ha="center", va="center", fontsize=7.5,
                color=INK if (pd.isna(r["inc"]) or r["inc"] < 600) else "white")
ax.set_axis_off()
ax.set_title("Previsão 2026-27 — incidência por UF", loc="left", color=INK, fontsize=13)
save(fig, "mapa_estados_2026_27.png")

# 2) mapa municipal
gm = mun.merge(fq[["inc"]].reset_index(names="geocode"), on="geocode", how="left")
fig, ax = plt.subplots(figsize=(7.5, 7.5))
gm.plot(ax=ax, column=gm["inc"].clip(lower=1), cmap=SEQ, linewidth=0,
        norm=LogNorm(vmin=5, vmax=gm["inc"].quantile(0.99)), legend=True,
        missing_kwds={"color": "#dcdbd6"},
        legend_kwds={"label": "casos previstos / 100 mil hab. (mediana)", "shrink": 0.55,
                     "orientation": "horizontal", "pad": 0.02})
ufs.boundary.plot(ax=ax, color="white", linewidth=0.6)
ax.set_axis_off()
ax.set_title("Previsão 2026-27 — 5.570 municípios", loc="left", color=INK, fontsize=13)
save(fig, "mapa_municipios_2026_27.png")

# 3) curva nacional semanal 2026-27
x = pd.to_datetime(nat.index)
fig, ax = plt.subplots(figsize=(9, 3.6))
ax.fill_between(x, nat["lower_80"], nat["upper_80"], color=BLUE, alpha=0.15, lw=0, label="IC 80% (soma UFs)")
ax.fill_between(x, nat["lower_50"], nat["upper_50"], color=BLUE, alpha=0.30, lw=0, label="IC 50%")
ax.plot(x, nat["pred"], color=BLUE, lw=2, label="mediana")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v / 1e3:,.0f} mil".replace(",", ".")))
ax.grid(axis="y", color=GRID, lw=0.8)
ax.set_title("Casos semanais previstos — Brasil (sem ES), EW41/2026 → EW40/2027",
             loc="left", color=INK, fontsize=12)
ax.legend(frameon=False, loc="upper left", fontsize=9)
save(fig, "curva_nacional_2026_27.png")

# 4) previsto x observado (estados), 3 temporadas
fig, ax = plt.subplots(figsize=(6.2, 6))
colors = {"2022-23": BLUE, "2023-24": ORANGE, "2024-25": "#1baf7a"}
mk = {"2022-23": "o", "2023-24": "s", "2024-25": "^"}
for s, d in state.groupby("season"):
    ax.errorbar(d["obs_total"], d["q50"], yerr=[d["q50"] - d["q10"], d["q90"] - d["q50"]],
                fmt=mk[s], ms=7, color=colors[s], ecolor=colors[s], elinewidth=1, alpha=0.9,
                mec="white", mew=1, label=s)
lim = [state[["obs_total", "q10"]].min().min() * 0.5, state[["obs_total", "q90"]].max().max() * 2]
ax.plot(lim, lim, color=INK2, lw=1, ls="--")
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel("total observado na temporada"); ax.set_ylabel("total previsto (mediana, IC 80%)")
ax.grid(color=GRID, lw=0.6)
for _, r in state.iterrows():
    if abs(r["log_err"]) > np.log(4):
        ax.annotate(r["uf"], (r["obs_total"], r["q50"]), xytext=(4, 3), textcoords="offset points",
                    fontsize=7, color=INK2)
ax.legend(title="temporada", frameon=False, loc="upper left")
ax.set_title("Estados: previsto × observado", loc="left", color=INK, fontsize=12)
save(fig, "estados_prev_vs_obs.png")


# 5/6) barras de fator de erro (melhores / piores)
def bars(df, label_col, title, name, n=8):
    best, worst = df.head(n), df.tail(n)[::-1]
    fig, axes = plt.subplots(1, 2, figsize=(11, 0.42 * n + 1.2), sharex=False)
    for ax, d, col, ttl in [(axes[0], best, BLUE, "Melhores"), (axes[1], worst, RED, "Piores")]:
        y = np.arange(len(d))[::-1]
        ax.barh(y, d["fator_erro"], color=col, height=0.62)
        ax.set_yticks(y); ax.set_yticklabels(d[label_col], fontsize=9)
        for yi, (_, r) in zip(y, d.iterrows()):
            tag = "super" if r["vies"] > 0 else "sub"
            ax.text(r["fator_erro"], yi, f"  {r['fator_erro']:.2f}×  ({tag})", va="center",
                    fontsize=8, color=INK2)
        ax.set_xlim(1, d["fator_erro"].max() * 1.45)
        ax.set_title(ttl, loc="left", color=INK, fontsize=11)
        ax.tick_params(axis="y", length=0)
        ax.grid(axis="x", color=GRID, lw=0.6)
        ax.set_xlabel("fator de erro médio do total (1 = perfeito)")
    fig.suptitle(title, x=0.01, ha="left", color=INK, fontsize=12)
    fig.tight_layout()
    save(fig, name)


srank["label"] = srank.index
bars(srank, "label", "Estados — erro do total da temporada (média 2022-23 a 2024-25)",
     "ranking_estados.png", n=6)
crank["label"] = crank["name"] + "-" + crank["uf"]
bars(crank, "label", f"Cidades ≥ {MIN_POP_RANK // 1000} mil hab. (≥ {MIN_OBS_RANK} casos/temp.) — erro do total da temporada",
     "ranking_cidades.png", n=8)

# 7) modelo x baselines (fator de erro mediano) — cidades >=100k e estados
fig, axes = plt.subplots(1, 2, figsize=(10, 3.4))
for ax, d, ttl in [(axes[0], summ_big, f"Cidades ≥ {MIN_POP_RANK // 1000} mil"), (axes[1], summ_state, "Estados")]:
    xs = np.arange(len(d)); w = 0.26
    for k, (col, lab, c) in enumerate([("fator_erro_mediano", "TFT + Richards", BLUE),
                                       ("fator_erro_ult_temp", "repete temporada anterior", "#9d9c97"),
                                       ("fator_erro_med3", "mediana 3 temporadas", "#c9c8c2")]):
        ax.bar(xs + (k - 1) * w, d[col], width=w - 0.03, color=c, label=lab)
        for xi, v in zip(xs, d[col]):
            ax.text(xi + (k - 1) * w, v, f"{v:.1f}", ha="center", va="bottom", fontsize=7.5, color=INK2)
    ax.set_xticks(xs); ax.set_xticklabels(d.index)
    ax.set_title(ttl, loc="left", color=INK, fontsize=11)
    ax.grid(axis="y", color=GRID, lw=0.6); ax.set_ylim(1, None)
    ax.set_ylabel("fator de erro mediano do total")
axes[0].legend(frameon=False, fontsize=8, loc="upper left")
fig.tight_layout()
save(fig, "modelo_vs_baselines.png")

# ------------------------------------------------------------------ resumo
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print("RHO =", RHO)
print("\n== todos os municípios\n", summ_all.round(3))
print(f"\n== municípios >= {MIN_POP_RANK}\n", summ_big.round(3))
print("\n== estados\n", summ_state.round(3))
print("\n== ranking estados\n", srank.round(3).to_string())
print("\n== cidades: melhores\n", crank.head(10).round(3).to_string())
print("\n== cidades: piores\n", crank.tail(10).round(3).to_string())
print("\n== previsão 2026-27 por UF\n", fs.round(1).to_string())
print("\nBrasil (sem ES) 2026-27: mediana da soma semanal =", round(nat["pred"].sum()),
      "| soma das medianas UF =", round(fs["q50"].sum()), "| pico semana:", nat["pred"].idxmax())
print("\n== top municípios 2026-27 (casos)\n",
      fq.sort_values("q50", ascending=False).head(10)[["name", "uf", "q10", "q50", "q90", "inc"]].round(0))
