"""
Pattern Blue v3 — inferência dos dois checkpoints de cada corte.

Saída: outputs/params/v3/params_<tag>_full.parquet (todos os dados) e params_<tag>_best.parquet (só etapa 1)
Uso (a partir de src/):  python infer_v3.py test4 test3 ...   (pula o que já existe)
"""
import os
import sys
import warnings
import numpy as np
import pandas as pd
import torch
from pytorch_forecasting import TemporalFusionTransformer, TimeSeriesDataSet

import common as C
import common_v3 as V

warnings.filterwarnings("ignore")
torch.set_float32_matmul_precision("medium")


def predict_cut(tag, base):
    variants = {v: f"{V.PARAMS_DIR}/params_{tag}_{v}.parquet" for v in ["full", "best"]}
    variants = {v: p for v, p in variants.items() if not os.path.exists(p)}
    if not variants:
        return
    year = C.cut_year(tag)
    frame, tgt = V.build_training_frame(base, year)
    norm = C.fit_normalizer(tgt)
    real = frame[frame["date"] <= C.cut_date(year)]
    template = V.build_dataset(real, norm)
    pred_ds = TimeSeriesDataSet.from_dataset(template, frame, predict=True, stop_randomization=True)
    dl = pred_ds.to_dataloader(train=False, batch_size=1024, num_workers=0)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    for variant, path in variants.items():
        model = TemporalFusionTransformer.load_from_checkpoint(f"{V.CKPT_ROOT}/{tag}/{variant}.ckpt", map_location=device)
        model.eval()
        out = model.predict(dl, mode="quantiles", return_index=True, trainer_kwargs=dict(logger=False, enable_progress_bar=False))
        preds, index = out.output, out.index
        assert (index["time_idx"] == frame["time_idx"].max()).all(), "decoder não está na EW26 do corte"
        geocodes = index["geocode"].astype(str).to_numpy()

        def mat(name):
            return np.sort(np.asarray(preds[C.TARGETS.index(name)].float().cpu()).reshape(len(geocodes), -1), axis=1)

        res = {"total_cases": np.expm1(mat("log_total_cases")).clip(min=0), "alpha": mat("alpha").clip(1e-3, 0.999),
               "beta": mat("beta").clip(1e-6, None), "peak_week": mat("peak_week").clip(0, 52)}
        tbl = pd.DataFrame({"geocode": np.repeat(geocodes, len(C.QUANTILE_LEVELS)),
                            "q": np.tile(C.QUANTILE_LEVELS, len(geocodes)), **{k: v.ravel() for k, v in res.items()}})
        med = tbl[tbl["q"] == 0.5]
        spread = tbl[tbl["q"] == 0.9].set_index("geocode")["alpha"] - tbl[tbl["q"] == 0.1].set_index("geocode")["alpha"]
        print(f"{tag} {variant}: municípios {tbl['geocode'].nunique()} | soma medianas {med['total_cases'].sum():,.0f} | "
              f"pico mediano {med['peak_week'].median():.1f} | largura q10-q90 de alpha {spread.median():.3f}", flush=True)
        os.makedirs(V.PARAMS_DIR, exist_ok=True)
        tbl.to_parquet(path, index=False)


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    base = V.load_base()
    for tag in sys.argv[1:]:
        predict_cut(tag, base)


if __name__ == "__main__":
    main()
