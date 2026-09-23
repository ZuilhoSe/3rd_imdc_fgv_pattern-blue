"""
IMDC 2026 — INFERÊNCIA.

Para cada corte (common.CUTS), carrega models/checkpoints/<tag>/best.ckpt, monta a janela
de 52 semanas terminando na EW25/Y (+ linha sintética de decoder na EW26/Y, só com
covariáveis conhecidas) e prevê os descritores da temporada EW41/Y - EW40/Y+1 para
TODOS os municípios.

Saída: outputs/params/params_<tag>.parquet
       colunas -> geocode, q, total_cases, alpha, beta, peak_week (índice na temporada)

Uso: python run_inference.py [tags...]   (padrão: todas as que têm checkpoint)
"""
import os
import sys
import warnings
import numpy as np
import pandas as pd
import torch
from pytorch_forecasting import TimeSeriesDataSet, TemporalFusionTransformer

import common as C

warnings.filterwarnings("ignore")
OUT_DIR = "outputs/params"


def predict_cut(tag, base):
    year = C.CUTS[tag]
    ckpt = f"models/checkpoints/{tag}/best.ckpt"
    print(f"\n=== {tag}: corte EW{C.CUT_WEEK}/{year} -> temporada {year}-{year + 1} ===")
    frame, tgt = C.build_training_frame(base, year)
    norm = C.fit_normalizer(tgt)
    real = frame[frame["date"] <= C.cut_date(year)]
    template = C.build_dataset(real, norm)
    pred_ds = TimeSeriesDataSet.from_dataset(template, frame, predict=True, stop_randomization=True)
    dl = pred_ds.to_dataloader(train=False, batch_size=1024, num_workers=0)

    model = TemporalFusionTransformer.load_from_checkpoint(
        ckpt, map_location="cuda" if torch.cuda.is_available() else "cpu")
    model.eval()
    out = model.predict(dl, mode="quantiles", return_index=True)
    preds, index = out.output, out.index
    assert (index["time_idx"] == frame["time_idx"].max()).all(), "decoder não está na EW26 do corte"
    geocodes = index["geocode"].astype(str).to_numpy()

    def mat(name):
        return np.sort(np.asarray(preds[C.TARGETS.index(name)].float().cpu()).reshape(len(geocodes), -1), axis=1)

    res = {"total_cases": np.expm1(mat("log_total_cases")).clip(min=0),
           "alpha": mat("alpha").clip(1e-3, 0.999),
           "beta": mat("beta").clip(1e-6, None),
           "peak_week": mat("peak_week").clip(0, 52)}
    tbl = pd.DataFrame({
        "geocode": np.repeat(geocodes, len(C.QUANTILE_LEVELS)),
        "q": np.tile(C.QUANTILE_LEVELS, len(geocodes)),
        **{k: v.ravel() for k, v in res.items()},
    })
    med = tbl[tbl["q"] == 0.5]
    print(f"  municípios: {tbl['geocode'].nunique()} | total Brasil (soma medianas): {med['total_cases'].sum():,.0f}"
          f" | pico mediano (índice): {med['peak_week'].median():.1f}")
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"params_{tag}.parquet")
    tbl.to_parquet(path, index=False)
    print(f"  salvo -> {path}")


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    tags = sys.argv[1:] or [t for t in C.CUTS if os.path.exists(f"models/checkpoints/{t}/best.ckpt")]
    base = C.load_base()
    for tag in tags:
        predict_cut(tag, base)


if __name__ == "__main__":
    main()
