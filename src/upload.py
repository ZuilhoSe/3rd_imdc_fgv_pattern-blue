"""
IMDC 2026 — UPLOAD das submissões de validação (dengue) para a plataforma Mosqlimate.

Percorre os CSVs gerados por build_submissions.py e envia uma predição por unidade
geográfica, por teste de validação, via mosqlient.upload_prediction (v2.5.x).

Assinatura real (mosqlient 2.5.2):
  upload_prediction(api_key, repository, disease, description, commit, prediction,
                    adm_level, case_definition='probable', published=True,
                    adm_0='BRA', adm_1=None, adm_2=None, adm_3=None)
  - repository:  "owner/repo"  (seu repositório público)
  - disease:     código CID-10 -> dengue = "A90"
  - adm_level:   1 (estado) ou 2 (município)
  - adm_1 / adm_2: INTEIROS (código IBGE da UF / geocode do município)
  - prediction:  DataFrame com date, pred, lower/upper_{50,80,90,95}

SEGURANÇA: começa em DRY_RUN (valida e mostra o que seria enviado, sem enviar).
Só envia de verdade quando você puser DRY_RUN = False.
"""
import os
import glob
import time
import pandas as pd
import imdc_submission as S

# ============================ CONFIG (preencha) ============================
API_KEY    = "X-UID-Key:ZuilhoSe:bbfa2e47-c0d8-4b8f-999d-5ab596d7ec25"
REPOSITORY = "ZuilhoSe/Pattern-Blue"
COMMIT     = "844f32d068d4f915ced17f33062171a74637adb5"
DISEASE    = "A90"

SUB_DIR    = "outputs/submissions"
TESTS      = [(1, 2022), (2, 2023), (3, 2024), (4, 2025)]

DRY_RUN    = True
PUBLISHED  = True
CASE_DEF   = "probable"
SLEEP      = 1.0
MANIFEST   = "outputs/upload_manifest.csv"
# ===========================================================================

UF_SIGLA_TO_CODE = {
    "RO":11,"AC":12,"AM":13,"RR":14,"PA":15,"AP":16,"TO":17,
    "MA":21,"PI":22,"CE":23,"RN":24,"PB":25,"PE":26,"AL":27,"SE":28,"BA":29,
    "MG":31,"ES":32,"RJ":33,"SP":35,
    "PR":41,"SC":42,"RS":43,"MS":50,"MT":51,"GO":52,"DF":53,
}


def load_manifest():
    if os.path.exists(MANIFEST):
        return pd.read_csv(MANIFEST, dtype=str)
    return pd.DataFrame(columns=["challenge", "test", "unit", "status", "msg"])


def already_ok(man, challenge, test, unit):
    m = man[(man.challenge == challenge) & (man.test == str(test)) & (man.unit == str(unit))]
    return (m["status"] == "ok").any()


def do_upload(df, adm_level, adm_1, adm_2, description):
    import mosqlient
    return mosqlient.upload_prediction(
        api_key=API_KEY, repository=REPOSITORY, disease=DISEASE,
        description=description, commit=COMMIT, prediction=df,
        adm_level=adm_level, case_definition=CASE_DEF, published=PUBLISHED,
        adm_0="BRA", adm_1=adm_1, adm_2=adm_2,
    )


def process_unit(challenge, test, year, unit, csv_path, adm_level, man, results):
    if already_ok(man, challenge, test, unit):
        print(f"    [{unit}] já enviado (skip)"); return
    df = pd.read_csv(csv_path)
    ok, errs = S.validate(df, year, verbose=False)
    if not ok:
        print(f"    [{unit}] ❌ inválido: {errs}")
        results.append((challenge, test, unit, "invalido", ";".join(errs))); return

    if adm_level == 1:
        adm_1, adm_2 = UF_SIGLA_TO_CODE[unit], None
    else:
        adm_1, adm_2 = None, int(unit)
    desc = f"3rd IMDC dengue {'UF' if adm_level==1 else 'municipio'} " \
           f"| validacao teste {test} ({year}-{year+1}) | {unit}"

    if DRY_RUN:
        print(f"    [{unit}] ✅ válido — DRY_RUN (adm_level={adm_level}, "
              f"adm_1={adm_1}, adm_2={adm_2}, {len(df)} semanas)")
        results.append((challenge, test, unit, "dry_run", "")); return
    try:
        do_upload(df, adm_level, adm_1, adm_2, desc)
        print(f"    [{unit}] ⬆️ enviado")
        results.append((challenge, test, unit, "ok", ""))
    except Exception as e:
        print(f"    [{unit}] ⚠️ falha no envio: {e}")
        results.append((challenge, test, unit, "erro", str(e)[:300]))
    time.sleep(SLEEP)


def main():
    if not DRY_RUN:
        import inspect, mosqlient
        print("assinatura:", inspect.signature(mosqlient.upload_prediction), "\n")

    man = load_manifest()
    results = []
    for test, year in TESTS:
        print(f"\n===== Teste {test} — temporada {year}-{year+1} =====")
        # cidade (adm_level 2)
        cdir = os.path.join(SUB_DIR, "dengue_city", f"test{test}_{year}")
        print(f"  [CIDADE] {cdir}")
        for f in sorted(glob.glob(os.path.join(cdir, "*.csv"))):
            if os.path.basename(f).startswith("_"):  # pula agregados _todas
                continue
            geocode = os.path.splitext(os.path.basename(f))[0]
            process_unit("dengue_city", test, year, geocode, f, 2, man, results)
        # estado (adm_level 1)
        sdir = os.path.join(SUB_DIR, "dengue_state", f"test{test}_{year}")
        print(f"  [ESTADO] {sdir}")
        for f in sorted(glob.glob(os.path.join(sdir, "*.csv"))):
            if os.path.basename(f).startswith("_"):
                continue
            uf = os.path.splitext(os.path.basename(f))[0]
            process_unit("dengue_state", test, year, uf, f, 1, man, results)

    # atualiza manifesto (append + dedup por challenge/test/unit mantendo o último)
    new = pd.DataFrame(results, columns=["challenge", "test", "unit", "status", "msg"]).astype(str)
    full = pd.concat([man, new], ignore_index=True) if len(man) else new
    full = full.drop_duplicates(subset=["challenge", "test", "unit"], keep="last")
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    full.to_csv(MANIFEST, index=False)
    print(f"\nresumo por status:\n{full['status'].value_counts().to_string()}")
    print(f"manifesto -> {MANIFEST}")
    if DRY_RUN:
        print("\n⚠️ DRY_RUN ativo: nada foi enviado. Ponha DRY_RUN=False para enviar.")


if __name__ == "__main__":
    main()