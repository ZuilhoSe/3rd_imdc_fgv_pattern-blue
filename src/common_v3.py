"""
Pattern Blue v3 — mesma arquitetura e mesma formulação da versão submetida (common.py), com:
  * todas as variáveis disponíveis (ver listas abaixo);
  * perda de forma só nas temporadas com ajuste Richards: nas demais, alpha, beta e pico são imputados
    por medianas, e treinar neles empurra as cabeças de forma para a mediana;
  * tags e artefatos separados, para não tocar nos modelos submetidos.
"""
import numpy as np
import pandas as pd
from pytorch_forecasting import TimeSeriesDataSet
from pytorch_forecasting.metrics import MultiLoss, QuantileLoss

import common as C

BASE_PATH = "../data/processed/base_weekly_v3.parquet"
TARGETS_PATH = "../data/processed/season_targets_v3.parquet"
CKPT_ROOT = "models/checkpoints/v3"
LOG_ROOT = "models/logs/v3"
PARAMS_DIR = "outputs/params/v3"

TIME_VARYING_KNOWN_REALS = C.TIME_VARYING_KNOWN_REALS + ["forecast_umid_med"]
TIME_VARYING_UNKNOWN_REALS = C.TIME_VARYING_UNKNOWN_REALS + [
    "temp_min", "temp_max", "precip_min", "precip_max", "pressure_med", "rel_humid_min", "rel_humid_max",
    "thermal_range", "rainy_days", "enso", "iod", "pdo", "log_casos_chik", "log_access", "has_access"]
STATIC_CATEGORICALS = C.STATIC_CATEGORICALS + ["regional_geocode"]
WEIGHT = "shape_weight"


class ShapeMaskedLoss(MultiLoss):
    """o total usa todas as amostras; alpha, beta e pico só as com ajuste Richards (peso em shape_weight)."""

    @staticmethod
    def _y(idx, y_actual):
        return (y_actual[0][idx], y_actual[1] if idx > 0 else None)

    def update(self, y_pred, y_actual, **kwargs):
        for idx, metric in enumerate(self.metrics):
            metric.update(y_pred[idx], self._y(idx, y_actual))

    def forward(self, y_pred, y_actual, **kwargs):
        res = [metric(y_pred[idx], self._y(idx, y_actual)) * self.weights[idx] for idx, metric in enumerate(self.metrics)]
        return torch_sum(res)


def torch_sum(values):
    total = values[0]
    for v in values[1:]:
        total = total + v
    return total


def make_loss():
    return ShapeMaskedLoss([QuantileLoss() for _ in C.TARGETS])


def load_base():
    df = pd.read_parquet(BASE_PATH)
    df["geocode"] = df["geocode"].astype(str)
    for c in STATIC_CATEGORICALS:
        df[c] = df[c].astype(str)
    df["log_casos"] = np.log1p(df["casos"].clip(lower=0))
    df["log_incidence"] = np.log1p(df["incidence"].clip(lower=0))
    df["target_season"] = df["season"] + 1
    return df


def build_training_frame(df, year):
    """como common.build_training_frame, com as variáveis novas e o peso da perda de forma."""
    targets = pd.read_parquet(TARGETS_PATH)
    tgt = C.season_targets_for_cut(year, targets)
    sub = df[df["date"] <= C.cut_date(year)]
    dec = C.decoder_rows(sub, year, df)
    # decoder_rows trata temperatura e chuva; a umidade prevista segue a mesma regra
    fut = df[(df["year"] == dec["year"].iloc[0]) & (df["month"] == dec["month"].iloc[0])]
    if len(fut):
        fc = fut.groupby("geocode")["forecast_umid_med"].first()
        dec["forecast_umid_med"] = dec["geocode"].map(fc).fillna(dec["forecast_umid_med"])
    frame = C.attach_targets(pd.concat([sub, dec], ignore_index=True), tgt)

    fit = tgt.rename(columns={"season": "target_season"})[["geocode", "target_season", "has_fit"]]
    frame = frame.merge(fit, on=["geocode", "target_season"], how="left")
    share = max(float(tgt["has_fit"].mean()), 1e-3)   # mantém a escala média da perda de forma
    frame[WEIGHT] = (frame["has_fit"].astype("boolean").fillna(False).astype(bool) / share).astype("float32")
    frame = frame.sort_values(["geocode", "time_idx"]).reset_index(drop=True)

    keep = (["geocode", "date", "time_idx", "week_of_year", "season", "target_season", "has_target", WEIGHT]
            + STATIC_CATEGORICALS + TIME_VARYING_KNOWN_REALS + TIME_VARYING_UNKNOWN_REALS + C.TARGETS)
    frame = frame[list(dict.fromkeys(keep))]
    fl = frame.select_dtypes("float64").columns
    frame[fl] = frame[fl].astype("float32")
    return frame, tgt


def build_dataset(frame, normalizer):
    return TimeSeriesDataSet(
        frame, time_idx="time_idx", target=C.TARGETS, group_ids=["geocode"], weight=WEIGHT,
        min_encoder_length=C.MIN_ENCODER_LENGTH, max_encoder_length=C.MAX_ENCODER_LENGTH,
        min_prediction_length=C.MAX_PRED_LENGTH, max_prediction_length=C.MAX_PRED_LENGTH,
        static_categoricals=STATIC_CATEGORICALS, static_reals=[],
        time_varying_known_reals=TIME_VARYING_KNOWN_REALS,
        time_varying_unknown_reals=TIME_VARYING_UNKNOWN_REALS,
        allow_missing_timesteps=True, target_normalizer=normalizer,
        add_relative_time_idx=True, add_target_scales=True, add_encoder_length=True,
    )
