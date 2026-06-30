import os
import warnings
import pandas as pd
import numpy as np
import torch
import lightning.pytorch as pl
from lightning.pytorch.callbacks import EarlyStopping, LearningRateMonitor, ModelCheckpoint
from lightning.pytorch.loggers import TensorBoardLogger
from pytorch_forecasting import TimeSeriesDataSet, TemporalFusionTransformer
from pytorch_forecasting.data import GroupNormalizer, MultiNormalizer
from pytorch_forecasting.metrics import MultiLoss, QuantileLoss, MAE

torch.set_float32_matmul_precision('medium')
warnings.filterwarnings("ignore")

DATA_PATH = "../data/processed/dataset_tft_completo.parquet"
BATCH_SIZE = 512
MAX_EPOCHS = 30
LEARNING_RATE = 0.03
GRADIENT_CLIP_VAL = 0.1

TARGETS = ["R0", "peak_week", "log_total_cases", "alpha", "beta", "gamma"]

TIME_VARYING_KNOWN_REALS = [
    "time_idx", "week_cycle", "sin_week_cycle", "cos_week_cycle", "log_pop",
    "forecast_temp_med", "forecast_precip_tot"  # Se você tiver a previsão climática
]

TIME_VARYING_UNKNOWN_REALS = [
    "casos", "incidence",
    "temp_med", "precip_med", "rel_humid_med"
    # "enso", "iod",
    # "tda_entropy_H1", "tda_amplitude_H1"
]

STATIC_CATEGORICALS = ["uf", "koppen", "biome", "macroregion_name"]
STATIC_REALS = []


def load_and_clean_data():
    print("⏳ Carregando dados...")
    data = pd.read_parquet(DATA_PATH)

    data["time_idx"] = data["time_idx"].astype(int)

    for col in STATIC_CATEGORICALS:
        data[col] = data[col].astype(str)

    print(f"Linhas antes da limpeza final: {len(data)}")

    # ==========================================
    # RAIO-X DOS NULOS (Adicione este bloco)
    # ==========================================
    colunas_verificar = TARGETS + TIME_VARYING_UNKNOWN_REALS + TIME_VARYING_KNOWN_REALS
    print("\n--- RAIO-X DE NULOS ---")
    nulos = data[colunas_verificar].isna().sum()
    print(nulos[nulos > 0])  # Vai imprimir apenas as colunas que têm algum NaN
    print("-----------------------\n")
    # ==========================================

    data = data.dropna(subset=colunas_verificar)
    print(f"Linhas para treino: {len(data)}")

    data["geocode"] = data["geocode"].astype(str)

    return data


def train():
    # 1. Preparar Dados
    data = load_and_clean_data()

    max_prediction_length = 1
    max_encoder_length = 52
    training_cutoff = data["time_idx"].max() - max_prediction_length

    print("🛠️ Configurando TimeSeriesDataSet (Isso pode demorar alguns minutos)...")

    target_normalizer = MultiNormalizer([
        GroupNormalizer(groups=["geocode"], transformation="softplus"),  # R0
        GroupNormalizer(groups=["geocode"], transformation="softplus"),  # peak_week
        GroupNormalizer(groups=["geocode"], transformation=None),  # log_total_cases
        GroupNormalizer(groups=["geocode"], transformation="logit"),  # alpha
        GroupNormalizer(groups=["geocode"], transformation="softplus"),  # beta
        GroupNormalizer(groups=["geocode"], transformation="softplus")  # gamma (NOVO)
    ])

    training_dataset = TimeSeriesDataSet(
        data[lambda x: x.time_idx <= training_cutoff],
        time_idx="time_idx",
        target=TARGETS,
        group_ids=["geocode"],
        min_encoder_length=20,
        max_encoder_length=max_encoder_length,
        min_prediction_length=max_prediction_length,
        max_prediction_length=max_prediction_length,

        static_categoricals=STATIC_CATEGORICALS,
        static_reals=STATIC_REALS,
        time_varying_known_reals=TIME_VARYING_KNOWN_REALS,
        time_varying_unknown_reals=TIME_VARYING_UNKNOWN_REALS,

        allow_missing_timesteps=True,
        target_normalizer=target_normalizer,
        add_relative_time_idx=True,
        add_target_scales=True,
        add_encoder_length=True,
    )

    validation = TimeSeriesDataSet.from_dataset(
        training_dataset,
        data,
        predict=True,
        stop_randomization=True
    )

    train_dataloader = training_dataset.to_dataloader(
        train=True,
        batch_size=BATCH_SIZE,
        num_workers=1
    )
    val_dataloader = validation.to_dataloader(
        train=False,
        batch_size=BATCH_SIZE * 2,
        num_workers=0
    )

    print("Initializing TFT")

    losses = [QuantileLoss(), QuantileLoss(), QuantileLoss(), QuantileLoss(), QuantileLoss(), QuantileLoss()]

    tft = TemporalFusionTransformer.from_dataset(
        training_dataset,
        learning_rate=LEARNING_RATE,
        hidden_size=32,
        attention_head_size=2,
        dropout=0.1,
        hidden_continuous_size=16,
        output_size=[7, 7, 7, 7, 7, 7],
        loss=MultiLoss(losses),
        log_interval=-1,
        reduce_on_plateau_patience=4,
    )

    print(f"Params: {tft.size() / 1e3:.1f}k")

    checkpoint_callback = ModelCheckpoint(
        dirpath="models/checkpoints/",
        filename="tft-{epoch:02d}-{val_loss:.2f}",
        monitor="val_loss",
        mode="min",
        save_top_k=1
    )

    early_stop_callback = EarlyStopping(
        monitor="val_loss",
        min_delta=1e-4,
        patience=5,
        verbose=True,
        mode="min"
    )

    trainer = pl.Trainer(
        max_epochs=MAX_EPOCHS,
        accelerator="gpu",
        devices=1,
        precision="bf16-mixed",  # <--- ATIVA OS TENSOR CORES DA RTX
        limit_train_batches=2000,  # <--- Acelera o fim da época
        limit_val_batches=500,  # <--- Acelera a validação
        gradient_clip_val=GRADIENT_CLIP_VAL,
        callbacks=[early_stop_callback, checkpoint_callback, LearningRateMonitor()],
        logger=TensorBoardLogger("models/logs")
    )

    print("Traning")
    trainer.fit(
        tft,
        train_dataloaders=train_dataloader,
        val_dataloaders=val_dataloader,
    )

    best_model_path = trainer.checkpoint_callback.best_model_path
    print(f"Best model saved to: {best_model_path}")

    best_tft = TemporalFusionTransformer.load_from_checkpoint(best_model_path, )

    return best_tft


if __name__ == "__main__":
    model = train()