"""
Pattern Blue v4 — mesma arquitetura e código do v3 (common_v3, train_v3, infer_v3), com:
  * previsão climática sazonal de junho (jul-set e out-dez) como variáveis conhecidas;
  * acumulado da temporada em curso e total da temporada anterior como variáveis observadas;
  * taxa de aprendizado 0,001 (ajuste fino 0,0001), até 50 épocas, paciência 8.
Protocolo: docs/evaluation_protocol_v4.md. Importar este módulo ANTES de train_v3/infer_v3.
"""
import common_v3 as V

V.BASE_PATH = "../data/processed/base_weekly_v4.parquet"
V.CKPT_ROOT = "models/checkpoints/v4"
V.LOG_ROOT = "models/logs/v4"
V.PARAMS_DIR = "outputs/params/v4"

SEASONAL_FORECAST = [f"fc_{p}_{v}" for p in ["pre", "early"] for v in ["temp", "umid", "precip"]]
SEASON_STATE = ["cum_log_casos", "cum_log_incidence", "prev_season_log_total"]
if SEASONAL_FORECAST[0] not in V.TIME_VARYING_KNOWN_REALS:
    V.TIME_VARYING_KNOWN_REALS = V.TIME_VARYING_KNOWN_REALS + SEASONAL_FORECAST
    V.TIME_VARYING_UNKNOWN_REALS = V.TIME_VARYING_UNKNOWN_REALS + SEASON_STATE

LEARNING_RATE = 0.001
FULL_LR = 0.0001


def configure_training(train_module):
    train_module.LEARNING_RATE = LEARNING_RATE
    train_module.FULL_LR = FULL_LR
