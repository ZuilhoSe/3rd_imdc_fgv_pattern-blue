"""
IMDC 2026 — MONTAGEM DAS SUBMISSÕES (usa imdc_submission.py, já testado).

Lê as tabelas de parâmetros (outputs/params/params_test{k}_{Y}.parquet), reconstrói
as curvas semanais e gera:
  - DENGUE CIDADE  : 15 cidades selecionadas
  - DENGUE ESTADO  : todas as UFs, exceto ES (agregando municípios -> UF)
para cada um dos 4 testes de validação. Cada arquivo já sai no formato exigido
(date, pred, lower/upper_{50,80,90,95}) e é validado contra as regras 4.2.
"""
import os
import numpy as np
import pandas as pd
import imdc_submission as S

PARAMS_DIR = "outputs/params"
OUT_DIR    = "outputs/submissions"
QS = [0.02, 0.10, 0.25, 0.50, 0.75, 0.90, 0.98]  # deve casar com run_inference.QUANTILE_LEVELS

TESTS = [(1, 2022), (2, 2023), (3, 2024), (4, 2025)]

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
    "11":"RO","12":"AC","13":"AM","14":"RR","15":"PA","16":"AP","17":"TO",
    "21":"MA","22":"PI","23":"CE","24":"RN","25":"PB","26":"PE","27":"AL","28":"SE","29":"BA",
    "31":"MG","32":"ES","33":"RJ","35":"SP",
    "41":"PR","42":"SC","43":"RS","50":"MS","51":"MT","52":"GO","53":"DF",
}
EXCLUDE_UF = "ES"


def load_params(k, year):
    df = pd.read_parquet(os.path.join(PARAMS_DIR, f"params_test{k}_{year}.parquet"))
    df["geocode"] = df["geocode"].astype(str)
    return df


def rows_by_geocode(df):
    """dict geocode -> {param: array(7,) ordenado por quantil}."""
    df = df.sort_values(["geocode", "q"])
    out = {}
    for gc, g in df.groupby("geocode"):
        out[gc] = {p: g[p].to_numpy(float) for p in S.PARAMS}
    return out


def stack_uf(rows, geocodes):
    """empilha {param: array(M,7)} para uma lista de municípios."""
    return {p: np.vstack([rows[gc][p] for gc in geocodes]) for p in S.PARAMS}


def main():
    for k, year in TESTS:
        print(f"\n############ TESTE {k} — temporada {year}-{year+1} ############")
        params = load_params(k, year)
        rows = rows_by_geocode(params)
        rows["_uf"] = None  # sentinela

        # ---------------- CIDADE ----------------
        city_dir = os.path.join(OUT_DIR, "dengue_city", f"test{k}_{year}")
        os.makedirs(city_dir, exist_ok=True)
        tidy_city = []
        print(f"[CIDADE] {len(DENGUE_CITIES)} cidades")
        for gc, name in DENGUE_CITIES.items():
            if gc not in rows:
                print(f"  ⚠️ {gc} ({name}) ausente na inferência — verifique o parquet/encoder")
                continue
            df = S.city_submission(year, rows[gc], QS, D=3000)
            ok, _ = S.validate(df, year, verbose=False)
            print(f"  {gc} {name:32s} {'✅' if ok else '❌'}")
            df.to_csv(os.path.join(city_dir, f"{gc}.csv"), index=False)
            df.insert(0, "geocode", gc); tidy_city.append(df)
        if tidy_city:
            pd.concat(tidy_city).to_csv(os.path.join(city_dir, "_todas_cidades.csv"), index=False)

        # ---------------- ESTADO ----------------
        state_dir = os.path.join(OUT_DIR, "dengue_state", f"test{k}_{year}")
        os.makedirs(state_dir, exist_ok=True)
        # agrupa municípios por UF (pelo geocode); exclui ES
        munis = [gc for gc in rows if gc not in ("_uf",)]
        by_uf = {}
        for gc in munis:
            uf = UF_CODE.get(gc[:2])
            if uf and uf != EXCLUDE_UF:
                by_uf.setdefault(uf, []).append(gc)
        print(f"[ESTADO] {len(by_uf)} UFs (exceto {EXCLUDE_UF})")
        tidy_state = []
        for uf, gcs in sorted(by_uf.items()):
            pq = stack_uf(rows, gcs)
            df = S.state_submission(year, pq, QS, D=1000)
            ok, _ = S.validate(df, year, verbose=False)
            print(f"  {uf}  {len(gcs):4d} munic.  {'✅' if ok else '❌'}  (pico p50 ~ {df['pred'].sum():.0f} casos/temp.)")
            df.to_csv(os.path.join(state_dir, f"{uf}.csv"), index=False)
            df.insert(0, "uf", uf); tidy_state.append(df)
        if tidy_state:
            pd.concat(tidy_state).to_csv(os.path.join(state_dir, "_todos_estados.csv"), index=False)

    print("\n✅ concluído. Arquivos em", OUT_DIR)
    print("   dengue_city/test{k}/<geocode>.csv  e  dengue_state/test{k}/<UF>.csv")


if __name__ == "__main__":
    main()
