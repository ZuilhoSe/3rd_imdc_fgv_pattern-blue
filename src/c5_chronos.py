"""
Candidato C5 do protocolo congelado (seção 4, emenda E3): Chronos-Bolt Small, zero-shot.

Para cada UF e cada cidade do desafio, a série semanal de casos até a EW25/Y é o contexto, e o modelo
prevê da EW26/Y até a EW40/Y+1. Ficam as semanas da temporada (EW41/Y a EW40/Y+1). Sem treino, sem
ajuste e sem olhar os cortes: os pesos são os publicados.

O Chronos-Bolt só aprendeu os quantis de 0,1 a 0,9. Para 0,025 e 0,05 a biblioteca repete o quantil
0,1, e para 0,95 e 0,975 repete o 0,9; os intervalos de 90% e 95% saem iguais ao de 80%. Fica assim,
como publicado, e isso pesa contra o C5 no WIS.

Uso (a partir de src/):  python c5_chronos.py [anos...]   # grava outputs/rolling/direct/c5_<Y>_<nível>.parquet
"""
import os
import sys
import warnings
import numpy as np
import pandas as pd
import torch
from chronos import BaseChronosPipeline

import common as C
import imdc_submission as S
import rolling_eval as R

MODEL = "amazon/chronos-bolt-small"
NAME = "c5"
YEARS = list(range(2015, 2025))


def horizon(year):
    """Semanas da EW26/Y até a EW40/Y+1, e onde começa a temporada dentro delas."""
    first = C.cut_date(year) + pd.Timedelta(days=7)
    season = pd.to_datetime(S.season_sundays(year))
    offset = (season[0] - first).days // 7
    assert (season[0] - first).days % 7 == 0 and offset >= 0
    return offset + len(season), offset


def forecast(pipe, df, year):
    cut = C.cut_date(year)
    H, offset = horizon(year)
    units, contexts = [], []
    for unit, g in df[df["date"] <= cut].groupby("unit"):
        g = g.sort_values("date")
        assert g["date"].iloc[-1] == cut, f"{unit}: série termina antes do corte"
        units.append(unit)
        contexts.append(torch.tensor(g["casos"].to_numpy(float), dtype=torch.float32))
    levels = [S.QLEVELS[c] for c in S.INTERVAL_ORDER]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")    # aviso de horizonte > 64 e de quantis fora de 0,1-0,9
        q, _ = pipe.predict_quantiles(contexts, prediction_length=H, quantile_levels=levels)
    q = q.numpy()[:, offset:, :].clip(min=0)          # (unidades, semanas da temporada, níveis)
    return {u: S.build_df(year, np.sort(q[i].T, axis=0)) for i, u in enumerate(units)}


def main(years):
    torch.manual_seed(0)
    pipe = BaseChronosPipeline.from_pretrained(MODEL, device_map="cpu", torch_dtype=torch.float32)
    truth = R.load_truth()
    os.makedirs(f"{R.OUT}/direct", exist_ok=True)
    for year in years:
        for level, df in truth.items():
            out = f"{R.OUT}/direct/{NAME}_{year}_{level}.parquet"
            if os.path.exists(out):
                continue
            frames = forecast(pipe, df, year)
            pd.concat([f.assign(unit=u) for u, f in frames.items()], ignore_index=True).to_parquet(out, index=False)
        print(f"{NAME} {year} ok", flush=True)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main([int(y) for y in sys.argv[1:]] or YEARS)
