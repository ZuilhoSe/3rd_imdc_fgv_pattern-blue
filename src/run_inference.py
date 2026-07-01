"""
IMDC 2026 — INFERÊNCIA (rode na sua máquina, onde estão o checkpoint e o parquet).

Para cada teste de validação, alimenta o encoder com a janela terminando no corte
(EW25 do ano Y) e lê os parâmetros do episcanner previstos para a PRÓXIMA temporada
(Y/Y+1) — que é como você deslocou o alvo no treino.

Saída: outputs/params/params_test{k}_{Y}.parquet
        colunas -> geocode, q, total_cases, alpha, beta, peak_week   (formato longo)

OBS: esta parte depende de pytorch_forecasting e do seu ambiente; deixei tudo
instrumentado com prints de verificação. Se algo quebrar, me mande o erro + a
saída dos prints e a versão (pip show pytorch_forecasting) que a gente ajusta.
"""
import os
import numpy as np
import pandas as pd
import torch
from pytorch_forecasting import TimeSeriesDataSet, TemporalFusionTransformer
from pytorch_forecasting.data import GroupNormalizer, MultiNormalizer

# ======================= CONFIG (espelha o seu treino) =======================
DATA_PATH   = "../data/processed/dataset_tft_completo.parquet"
CKPT_PATH   = "models/checkpoints/tft-epoch=08-val_loss=194.65.ckpt"
OUT_DIR     = "outputs/params"

TARGETS = ["R0", "peak_week", "log_total_cases", "alpha", "beta", "gamma"]
TIME_VARYING_KNOWN_REALS = ["time_idx", "week_cycle", "sin_week_cycle", "cos_week_cycle",
                            "log_pop", "forecast_temp_med", "forecast_precip_tot"]
TIME_VARYING_UNKNOWN_REALS = ["casos", "incidence", "temp_med", "precip_med", "rel_humid_med"]
STATIC_CATEGORICALS = ["uf", "koppen", "biome", "macroregion_name"]
MAX_ENCODER_LENGTH, MAX_PRED_LENGTH, MIN_ENCODER_LENGTH = 52, 1, 20

# quantis do QuantileLoss default do pytorch_forecasting (output_size=7)
QUANTILE_LEVELS = [0.02, 0.10, 0.25, 0.50, 0.75, 0.90, 0.98]

# cada teste: (id, ano_inicio_temporada_prevista, ano/semana do corte de dados)
#   teste 1: dados <= EW25/2022 -> prevê temporada 2022-2023
VALIDATION_TESTS = [
    (1, 2022, (2022, 25)),
    (2, 2023, (2023, 25)),
    (3, 2024, (2024, 25)),
    (4, 2025, (2025, 25)),
]
# =============================================================================


def cutoff_time_idx(df, year, week):
    """time_idx da última semana <= EW{week}/{year} (usa a coluna 'date')."""
    from epiweeks import Week
    limit = pd.Timestamp(Week(year, week, system="cdc").enddate())  # sábado da EW
    sub = df[pd.to_datetime(df["date"]) <= limit]
    return int(sub["time_idx"].max())


def build_base_dataset(df):
    """Recria o TimeSeriesDataSet de treino (mesma config) só para servir de molde."""
    tn = MultiNormalizer([
        GroupNormalizer(groups=["geocode"], transformation="softplus"),   # R0
        GroupNormalizer(groups=["geocode"], transformation="softplus"),   # peak_week
        GroupNormalizer(groups=["geocode"], transformation=None),         # log_total_cases
        GroupNormalizer(groups=["geocode"], transformation="logit"),      # alpha
        GroupNormalizer(groups=["geocode"], transformation="softplus"),   # beta
        GroupNormalizer(groups=["geocode"], transformation="softplus"),   # gamma
    ])
    return TimeSeriesDataSet(
        df, time_idx="time_idx", target=TARGETS, group_ids=["geocode"],
        min_encoder_length=MIN_ENCODER_LENGTH, max_encoder_length=MAX_ENCODER_LENGTH,
        min_prediction_length=MAX_PRED_LENGTH, max_prediction_length=MAX_PRED_LENGTH,
        static_categoricals=STATIC_CATEGORICALS, static_reals=[],
        time_varying_known_reals=TIME_VARYING_KNOWN_REALS,
        time_varying_unknown_reals=TIME_VARYING_UNKNOWN_REALS,
        allow_missing_timesteps=True, target_normalizer=tn,
        add_relative_time_idx=True, add_target_scales=True, add_encoder_length=True,
    )


def extract_quantiles(model, dataloader):
    """
    Retorna DataFrame longo: geocode, q, total_cases, alpha, beta, peak_week.
    mode='quantiles' já devolve na escala original de cada alvo.
    log_total_cases volta em log -> expm1 para virar total_cases.
    """
    out = model.predict(dataloader, mode="quantiles", return_index=True)
    # compat. entre versões do pytorch_forecasting:
    preds = getattr(out, "output", out[0] if isinstance(out, (tuple, list)) else out)
    index = getattr(out, "index", None)
    if index is None:  # fallback antigo
        _, index = out
    geocodes = index["geocode"].astype(str).to_numpy()

    def as_mat(target_name):
        i = TARGETS.index(target_name)
        t = preds[i]                      # (n_series, 1, 7)
        return np.asarray(t).reshape(len(geocodes), -1)  # (n_series, 7)

    log_tc = as_mat("log_total_cases")
    total_cases = np.expm1(log_tc)
    alpha  = as_mat("alpha")
    beta   = as_mat("beta")
    peak_w = as_mat("peak_week")

    rows = []
    for s, gc in enumerate(geocodes):
        for j, q in enumerate(QUANTILE_LEVELS):
            rows.append((gc, q, float(max(total_cases[s, j], 0)),
                         float(np.clip(alpha[s, j], 1e-3, 0.999)),
                         float(max(beta[s, j], 1e-6)),
                         float(np.clip(peak_w[s, j], 1, 53))))
    return pd.DataFrame(rows, columns=["geocode", "q", "total_cases", "alpha", "beta", "peak_week"])


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print("⏳ carregando parquet...")
    df = pd.read_parquet(DATA_PATH)
    df["geocode"] = df["geocode"].astype(str)
    for c in STATIC_CATEGORICALS:
        if c in df.columns:
            df[c] = df[c].astype(str)
    df["time_idx"] = df["time_idx"].astype(int)

    # Replica o pré-processamento do treino: descarta linhas com NaN nos alvos e nas
    # features do modelo. Isso (a) resolve o erro de NaN em temp_med e (b) mantém os
    # encoders/categorias idênticos aos vistos no treino (senão os embeddings de
    # uf/koppen/biome/macroregion desalinham e a previsão sai errada em silêncio).
    MODEL_COLS = TARGETS + TIME_VARYING_KNOWN_REALS + TIME_VARYING_UNKNOWN_REALS
    MODEL_COLS = [c for c in MODEL_COLS if c in df.columns]
    full = df.dropna(subset=MODEL_COLS).copy()
    print(f"linhas {len(df)} -> após dropna(model_cols) {len(full)} "
          f"| municípios: {full['geocode'].nunique()}")

    print("⏳ carregando checkpoint...")
    model = TemporalFusionTransformer.load_from_checkpoint(CKPT_PATH,
                map_location="cuda" if torch.cuda.is_available() else "cpu")
    model.eval()

    # molde do dataset (encoders/normalizers) a partir do frame equivalente ao treino
    base = build_base_dataset(full)

    for k, start_year, (cy, cw) in VALIDATION_TESTS:
        cut = cutoff_time_idx(full, cy, cw)
        print(f"\n=== Teste {k}: temporada {start_year}-{start_year+1} | corte EW{cw}/{cy} (time_idx={cut}) ===")
        sub = full[full["time_idx"] <= cut].copy()
        last = sub.groupby("geocode")["time_idx"].transform("max")
        sub = sub[last == cut]   # só séries cujo alvo (fit episcanner) existe na temporada-alvo
        print(f"  séries previsíveis neste corte: {sub['geocode'].nunique()}")
        pred_ds = TimeSeriesDataSet.from_dataset(base, sub, predict=True, stop_randomization=True)
        dl = pred_ds.to_dataloader(train=False, batch_size=512, num_workers=0)

        tbl = extract_quantiles(model, dl)
        # ---- VERIFICAÇÃO: espie 3 municípios; o pico previsto deve cair ~EW6-20 ----
        med = tbl[tbl["q"] == 0.5]
        print("  amostra (mediana) — geocode | total_cases | peak_week(EW) | alpha:")
        print(med.head(3).to_string(index=False))
        print(f"  municípios previstos: {tbl['geocode'].nunique()} | "
              f"peak_week mediano p50: {med['peak_week'].median():.1f}")

        path = os.path.join(OUT_DIR, f"params_test{k}_{start_year}.parquet")
        tbl.to_parquet(path, index=False)
        print(f"  salvo -> {path}")


if __name__ == "__main__":
    main()