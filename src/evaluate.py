"""
IMDC 2026 — AVALIAÇÃO das validações (WIS semanal, como no desafio).

  python evaluate.py tune            # calibra rho (correlação entre municípios no agregado UF)
                                     #   -> outputs/state_rho.json
  python evaluate.py <dir_submissoes> [rotulo]   # WIS de um conjunto de submissões
                                     #   (ex.: outputs/submissions ou a cópia da v1)

A temporada do teste 4 (2025-26) só tem dados até EW25/2026 -> avaliada parcialmente.
"""
import json
import os
import sys
import numpy as np
import pandas as pd

import build_submissions as B
import imdc_submission as S
from common import CUTS

ALPHAS = {"50": 0.5, "80": 0.2, "90": 0.1, "95": 0.05}
TESTS = [t for t in CUTS if t != "final"]


def wis(df, y):
    """WIS (Bracher et al. 2021) por semana: median + 4 intervalos."""
    m = df["pred"].to_numpy()
    total = 0.5 * np.abs(y - m)
    for k, a in ALPHAS.items():
        lo, hi = df[f"lower_{k}"].to_numpy(), df[f"upper_{k}"].to_numpy()
        total += a / 2 * ((hi - lo) + 2 / a * (lo - y) * (y < lo) + 2 / a * (y - hi) * (y > hi))
    return total / (len(ALPHAS) + 0.5)


def truth():
    b = pd.read_parquet("../data/processed/base_weekly.parquet", columns=["geocode", "date", "casos", "uf"])
    b["geocode"] = b["geocode"].astype(str)
    b["date"] = b["date"].dt.strftime("%Y-%m-%d")
    city = b[b["geocode"].isin(B.DENGUE_CITIES)].rename(columns={"geocode": "unit"})[["unit", "date", "casos"]]
    state = b.groupby(["uf", "date"], as_index=False)["casos"].sum().rename(columns={"uf": "unit"})
    return {"dengue_city": city, "dengue_state": state}


def score(frames, tr):
    """frames: {unit: df submissão}; tr: verdade (unit, date, casos) -> WIS médio por unidade."""
    out = {}
    for unit, df in frames.items():
        m = df.merge(tr[tr["unit"] == unit], on="date")
        if len(m):
            out[unit] = wis(m, m["casos"].to_numpy(float)).mean()
    return pd.Series(out)


def score_dir(sub_dir, label):
    tr = truth()
    rows = []
    for tag in TESTS:
        for kind in ["dengue_city", "dengue_state"]:
            d = os.path.join(sub_dir, kind, B.folder(tag))
            if not os.path.isdir(d):
                continue
            frames = {os.path.splitext(f)[0]: pd.read_csv(os.path.join(d, f))
                      for f in os.listdir(d) if not f.startswith("_")}
            s = score(frames, tr[kind])
            rows.append((label, tag, kind, s.mean(), s.median(), len(s)))
    res = pd.DataFrame(rows, columns=["modelo", "teste", "desafio", "wis_medio", "wis_mediana", "n"])
    print(res.to_string(index=False, float_format=lambda v: f"{v:,.1f}"))
    return res


def tune(rhos=(0.0, 0.2, 0.4, 0.6, 0.8)):
    tr = truth()["dengue_state"]
    tags = [t for t in TESTS if os.path.exists(os.path.join(B.PARAMS_DIR, f"params_{t}.parquet"))]
    res = {}
    for rho in rhos:
        vals = []
        for tag in tags:
            rows = B.load_rows(tag)
            # WIS relativo por UF (divide pela média de casos da UF) p/ não deixar SP/MG dominarem
            s = score(B.state_frames(rows, CUTS[tag], rho), tr)
            scale = tr.groupby("unit")["casos"].mean().reindex(s.index)
            vals.append((s / scale).mean())
        res[rho] = float(np.mean(vals))
        print(f"rho={rho:.1f}  WIS relativo médio (UFs, {len(tags)} testes) = {res[rho]:.4f}")
    best = min(res, key=res.get)
    json.dump({"rho": best, "scores": res, "tests": tags}, open(B.RHO_PATH, "w"), indent=2)
    print(f"-> rho = {best} salvo em {B.RHO_PATH}")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if sys.argv[1:2] == ["tune"]:
        tune()
    else:
        score_dir(sys.argv[1] if len(sys.argv) > 1 else B.OUT_DIR, sys.argv[2] if len(sys.argv) > 2 else "v2")
