"""
IMDC 2026 — MONTAGEM DAS SUBMISSÕES (usa imdc_submission.py).

Lê outputs/params/params_<tag>.parquet, reconstrói as curvas semanais e gera:
  - DENGUE CIDADE  : 15 cidades selecionadas
  - DENGUE ESTADO  : todas as UFs, exceto ES (soma de TODOS os municípios da UF)
para as 4 validações e a previsão final 2026-2027. Cada arquivo sai no formato exigido
(date, pred, lower/upper_{50,80,90,95}) e é validado.

Pastas: outputs/submissions/dengue_{city,state}/<test{k}_{Y} | final_2026>/
Uso: python build_submissions.py [tags...]   (padrão: todas com parâmetros)
"""
import json
import os
import sys
import numpy as np
import pandas as pd
import imdc_submission as S
from common import CUTS, QUANTILE_LEVELS as QS

PARAMS_DIR = "outputs/params"
OUT_DIR = "outputs/submissions"
RHO_PATH = "outputs/state_rho.json"   # gerado por evaluate.py (correlação entre municípios)

DENGUE_CITIES = {  # geocode -> nome (Optional Challenge 1)
    "2931350": "Teixeira de Freitas-BA", "2933307": "Vitoria da Conquista-BA",
    "2302503": "Brejo Santo-CE", "3119401": "Coronel Fabriciano-MG",
    "3549805": "Sao Jose do Rio Preto-SP", "3541406": "Presidente Prudente-SP",
    "1200401": "Rio Branco-AC", "1200203": "Cruzeiro do Sul-AC",
    "1716109": "Paraiso do Tocantins-TO", "4113700": "Londrina-PR",
    "4103701": "Cambe-PR", "4104808": "Cascavel-PR",
    "5201405": "Aparecida de Goiania-GO", "5102637": "Campo Novo do Parecis-MT",
    "5215231": "Novo Gama-GO",
}
UF_CODE = {  # 2 primeiros dígitos do geocode -> sigla
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE", "29": "BA",
    "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}
EXCLUDE_UF = "ES"
N_MUNICIPIOS = 5570


def folder(tag):
    year = CUTS[tag]
    return f"final_{year}" if tag == "final" else f"{tag}_{year}"


def load_rows(tag):
    df = pd.read_parquet(os.path.join(PARAMS_DIR, f"params_{tag}.parquet"))
    df["geocode"] = df["geocode"].astype(str)
    df = df.sort_values(["geocode", "q"])
    assert np.allclose(df["q"].unique(), QS), "quantis diferentes de common.QUANTILE_LEVELS"
    return {gc: {p: g[p].to_numpy(float) for p in S.PARAMS} for gc, g in df.groupby("geocode")}


def by_uf(rows):
    out = {}
    for gc in rows:
        uf = UF_CODE.get(gc[:2])
        if uf and uf != EXCLUDE_UF:
            out.setdefault(uf, []).append(gc)
    return out


def stack(rows, geocodes):
    return {p: np.vstack([rows[gc][p] for gc in geocodes]) for p in S.PARAMS}


def city_frames(rows, year):
    return {gc: S.city_submission(year, rows[gc], QS, D=3000) for gc in DENGUE_CITIES}


def state_frames(rows, year, rho):
    return {uf: S.state_submission(year, stack(rows, gcs), QS, D=1000, rho=rho)
            for uf, gcs in sorted(by_uf(rows).items())}


def build(tag, rho):
    year = CUTS[tag]
    print(f"\n############ {tag} — temporada {year}-{year + 1} (rho={rho}) ############")
    rows = load_rows(tag)
    assert len(rows) == N_MUNICIPIOS, f"esperava {N_MUNICIPIOS} municípios, veio {len(rows)}"
    for kind, frames, key in [("dengue_city", city_frames(rows, year), "geocode"),
                              ("dengue_state", state_frames(rows, year, rho), "uf")]:
        d = os.path.join(OUT_DIR, kind, folder(tag))
        os.makedirs(d, exist_ok=True)
        tidy = []
        for unit, df in frames.items():
            ok, errs = S.validate(df, year, verbose=False)
            assert ok, f"{kind} {unit}: {errs}"
            df.to_csv(os.path.join(d, f"{unit}.csv"), index=False)
            tidy.append(df.assign(**{key: unit}))
        allf = pd.concat(tidy)
        allf.to_csv(os.path.join(d, "_todas_cidades.csv" if kind == "dengue_city" else "_todos_estados.csv"), index=False)
        print(f"  {kind}: {len(frames)} unidades ✅ | soma das medianas na temporada: {allf['pred'].sum():,.0f}")


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    rho = json.load(open(RHO_PATH))["rho"] if os.path.exists(RHO_PATH) else 0.0
    tags = sys.argv[1:] or [t for t in CUTS if os.path.exists(os.path.join(PARAMS_DIR, f"params_{t}.parquet"))]
    for tag in tags:
        build(tag, rho)


if __name__ == "__main__":
    main()
