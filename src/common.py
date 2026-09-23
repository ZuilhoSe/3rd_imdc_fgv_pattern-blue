"""
IMDC 2026 — definições compartilhadas entre treino, inferência e submissão.

Formulação (corrigida):
  * uma amostra = janela de 52 semanas do município (encoder) + 1 semana de decoder na
    semana w do ano X; o alvo é o conjunto de descritores da temporada SEGUINTE
    (EW41/X -> EW40/X+1), i.e. season_da_linha + 1;
  * para o corte EW25/Y só se usam como alvo temporadas COMPLETAS antes do corte
    (temporada <= Y-1). Treino: alvos <= Y-2; early stopping: alvo = Y-1;
  * alvos: log_total_cases (total observado), alpha, beta, peak_week (índice na
    temporada, EW41 = 0). Temporadas sem ajuste Richards recebem forma imputada
    (mediana do município -> região de saúde -> UF -> global), só com dados <= corte;
  * normalizador dos alvos ajustado apenas nas temporadas conhecidas no corte.
"""
import numpy as np
import pandas as pd
from epiweeks import Week
from pytorch_forecasting import TimeSeriesDataSet
from pytorch_forecasting.data import GroupNormalizer, MultiNormalizer

BASE_PATH = "../data/processed/base_weekly.parquet"
TARGETS_PATH = "../data/processed/season_targets.parquet"

# tag -> ano Y do corte (dados até EW25/Y; prevê a temporada EW41/Y - EW40/Y+1)
CUTS = {"test1": 2022, "test2": 2023, "test3": 2024, "test4": 2025, "final": 2026}
CUT_WEEK = 25

TARGETS = ["log_total_cases", "alpha", "beta", "peak_week"]
SHAPE = ["alpha", "beta", "peak_week"]
QUANTILE_LEVELS = [0.02, 0.10, 0.25, 0.50, 0.75, 0.90, 0.98]  # QuantileLoss default

# time_idx fica fora: como covariável contínua deixava o modelo "decorar" cada ano
# (val_loss 2.82 -> 2.39 sem ele, no corte final)
TIME_VARYING_KNOWN_REALS = ["week_cycle", "sin_week_cycle", "cos_week_cycle",
                            "log_pop", "forecast_temp_med", "forecast_precip_tot"]
TIME_VARYING_UNKNOWN_REALS = ["log_casos", "log_incidence", "temp_med", "precip_med", "rel_humid_med"]
STATIC_CATEGORICALS = ["uf", "koppen", "biome", "macroregion_name"]
MAX_ENCODER_LENGTH, MIN_ENCODER_LENGTH, MAX_PRED_LENGTH = 52, 20, 1

TRAIN_DECODER_WEEKS = range(20, 33)   # semanas do ano usadas como decoder no treino (em torno da EW26)
VAL_DECODER_WEEK = 26                 # decoder das amostras de early stopping / inferência


def cut_date(year):
    return pd.Timestamp(Week(year, CUT_WEEK, system="cdc").startdate())


def load_base():
    df = pd.read_parquet(BASE_PATH)
    df["geocode"] = df["geocode"].astype(str)
    for c in STATIC_CATEGORICALS:
        df[c] = df[c].astype(str)
    df["log_casos"] = np.log1p(df["casos"].clip(lower=0))
    df["log_incidence"] = np.log1p(df["incidence"].clip(lower=0))
    df["target_season"] = df["season"] + 1
    return df


def season_targets_for_cut(year, targets=None):
    """alvos por (geocode, temporada) usando só temporadas completas até o corte (<= Y-1)."""
    t = pd.read_parquet(TARGETS_PATH) if targets is None else targets.copy()
    t["geocode"] = t["geocode"].astype(str)
    t = t[t["season"] <= year - 1].copy()
    t = t.rename(columns={"peak_idx": "peak_week"})
    t["log_total_cases"] = np.log1p(t["obs_total"])

    fits = t[t["has_fit"]]
    geo = pd.read_parquet(BASE_PATH, columns=["geocode", "uf", "regional_geocode"]).drop_duplicates("geocode")
    geo["geocode"] = geo["geocode"].astype(str)
    t = t.merge(geo, on="geocode", how="left")
    fits = fits.merge(geo, on="geocode", how="left")
    for c in SHAPE:
        for key in ["geocode", "regional_geocode", "uf"]:
            med = fits.groupby(key)[c].median()
            t[c] = t[c].fillna(t[key].map(med))
        t[c] = t[c].fillna(fits[c].median())
    t["alpha"] = t["alpha"].clip(0.01, 0.99)
    t["beta"] = t["beta"].clip(1e-3, None)
    t["peak_week"] = t["peak_week"].clip(0, 52)
    return t[["geocode", "season"] + TARGETS + ["has_fit"]]


def make_normalizer():
    return MultiNormalizer([
        GroupNormalizer(groups=["geocode"], transformation=None),       # log_total_cases
        GroupNormalizer(groups=["geocode"], transformation="logit"),    # alpha
        GroupNormalizer(groups=["geocode"], transformation="log"),      # beta
        GroupNormalizer(groups=["geocode"], transformation=None),       # peak_week (índice)
    ])


def attach_targets(df, tgt):
    """alvo da linha = descritores da temporada seguinte; sem alvo -> mediana do município (dummy)."""
    m = tgt.rename(columns={"season": "target_season"})[["geocode", "target_season"] + TARGETS]
    out = df.drop(columns=[c for c in TARGETS if c in df.columns]).merge(m, on=["geocode", "target_season"], how="left")
    out["has_target"] = out["log_total_cases"].notna()
    for c in TARGETS:
        med = tgt.groupby("geocode")[c].median()
        out[c] = out[c].fillna(out["geocode"].map(med)).fillna(tgt[c].median())
    return out.sort_values(["geocode", "time_idx"]).reset_index(drop=True)


def decoder_rows(df, year, full=None):
    """linha sintética EW26/Y por município: covariáveis conhecidas recalculadas, desconhecidas = EW25."""
    cd = cut_date(year)
    last = df[df["date"] == cd].copy()
    wk = Week.fromdate((cd + pd.Timedelta(days=7)).date(), system="cdc")
    last["date"] = cd + pd.Timedelta(days=7)
    last["time_idx"] += 1
    last["epiweek"] = int(wk.cdcformat())
    last["week_of_year"] = wk.week
    last["week_cycle"] = wk.week + 12 if wk.week < 41 else wk.week - 40
    last["sin_week_cycle"] = np.sin(2 * np.pi * last["week_cycle"] / 52)
    last["cos_week_cycle"] = np.cos(2 * np.pi * last["week_cycle"] / 52)
    last["year"], last["month"] = last["date"].dt.year, last["date"].dt.month
    last["season"] = year
    last["target_season"] = year + 1
    # previsão climática do mês do decoder (se já estiver na base, usa a da própria base)
    # (previsões emitidas até o mês anterior ao mês-alvo -> conhecidas no corte)
    full = df if full is None else full
    fut = full[(full["year"] == last["year"].iloc[0]) & (full["month"] == last["month"].iloc[0])]
    if len(fut):
        fc = fut.groupby("geocode")[["forecast_temp_med", "forecast_precip_tot"]].first()
        for c in fc.columns:
            last[c] = last["geocode"].map(fc[c]).fillna(last[c])
    return last


def build_training_frame(df, year):
    """dados até o corte + alvos; linha de decoder EW26/Y sintética p/ inferência."""
    tgt = season_targets_for_cut(year)
    sub = df[df["date"] <= cut_date(year)]
    sub = pd.concat([sub, decoder_rows(sub, year, df)], ignore_index=True)
    frame = attach_targets(sub, tgt)
    # só as colunas do modelo, em float32 (reduz ~pela metade a RAM do TimeSeriesDataSet)
    keep = (["geocode", "date", "time_idx", "week_of_year", "season", "target_season", "has_target"]
            + STATIC_CATEGORICALS + TIME_VARYING_KNOWN_REALS + TIME_VARYING_UNKNOWN_REALS + TARGETS)
    frame = frame[list(dict.fromkeys(keep))]
    fl = frame.select_dtypes("float64").columns
    frame[fl] = frame[fl].astype("float32")
    return frame, tgt


def fit_normalizer(tgt):
    """ajusta o normalizador só nas temporadas conhecidas (uma linha por município-temporada)."""
    rows = tgt.copy()
    norm = make_normalizer()
    norm.fit(rows[TARGETS], rows)
    return norm


def build_dataset(frame, normalizer):
    return TimeSeriesDataSet(
        frame, time_idx="time_idx", target=TARGETS, group_ids=["geocode"],
        min_encoder_length=MIN_ENCODER_LENGTH, max_encoder_length=MAX_ENCODER_LENGTH,
        min_prediction_length=MAX_PRED_LENGTH, max_prediction_length=MAX_PRED_LENGTH,
        static_categoricals=STATIC_CATEGORICALS, static_reals=[],
        time_varying_known_reals=TIME_VARYING_KNOWN_REALS,
        time_varying_unknown_reals=TIME_VARYING_UNKNOWN_REALS,
        allow_missing_timesteps=True, target_normalizer=normalizer,
        add_relative_time_idx=True, add_target_scales=True, add_encoder_length=True,
    )


def time_calendar(frame):
    """time_idx -> (semana do ano, temporada-alvo)."""
    cal = frame[["time_idx", "week_of_year", "target_season"]].drop_duplicates("time_idx").set_index("time_idx")
    return cal["week_of_year"], cal["target_season"]


def decoder_mask(decoded_index, frame, weeks, seasons):
    wk, ts = time_calendar(frame)
    t = decoded_index["time_idx_first_prediction"]
    return t.map(wk).isin(list(weeks)).to_numpy() & t.map(ts).isin(list(seasons)).to_numpy()
