"""
IMDC 2026 — TREINO do TFT (um modelo por corte, sem vazamento).

Para o corte EW25/Y (tags em common.CUTS):
  * treino: decoders nas semanas 20-32 do ano X, alvo = temporada X/X+1, com X+1 <= Y-2;
  * early stopping: decoder na EW26 do ano Y-2, alvo = temporada Y-2/Y-1 (última completa);
  * normalizador dos alvos ajustado só com temporadas <= Y-1.

Uso (a partir de src/):
  python train.py final            # só a previsão final
  python train.py test1 test2 ...  # validações
  python train.py all
Saída: models/checkpoints/<tag>/best.ckpt
"""
import os
import sys
import shutil
import warnings
import torch
import lightning.pytorch as pl
from lightning.pytorch.callbacks import EarlyStopping, LearningRateMonitor, ModelCheckpoint
from lightning.pytorch.loggers import TensorBoardLogger
from pytorch_forecasting import TemporalFusionTransformer
from pytorch_forecasting.metrics import MultiLoss, QuantileLoss

import common as C

torch.set_float32_matmul_precision("medium")
warnings.filterwarnings("ignore")

BATCH_SIZE = 256
MAX_EPOCHS = int(os.getenv("MAX_EPOCHS", "15"))
TRAIN_BATCHES_PER_EPOCH = 400
LEARNING_RATE = 0.003
GRADIENT_CLIP_VAL = 0.1
SEED = 42


def train_cut(tag, base):
    year = C.CUTS[tag]
    pl.seed_everything(SEED)
    print(f"\n==================== {tag}: corte EW{C.CUT_WEEK}/{year} ====================")
    frame, tgt = C.build_training_frame(base, year)
    norm = C.fit_normalizer(tgt)

    # dataset sem a linha sintética de decoder (ela só serve para a inferência)
    real = frame[frame["date"] <= C.cut_date(year)]
    full_ds = C.build_dataset(real, norm)
    idx = full_ds.decoded_index
    train_ds = full_ds.filter(lambda d: C.decoder_mask(d, real, C.TRAIN_DECODER_WEEKS, range(2000, year - 1)))
    val_ds = full_ds.filter(lambda d: C.decoder_mask(d, real, [C.VAL_DECODER_WEEK], [year - 1]))
    print(f"amostras: treino {len(train_ds)} | validação {len(val_ds)} (de {len(idx)})")

    train_dl = train_ds.to_dataloader(train=True, batch_size=BATCH_SIZE, num_workers=0)
    val_dl = val_ds.to_dataloader(train=False, batch_size=BATCH_SIZE * 4, num_workers=0)

    tft = TemporalFusionTransformer.from_dataset(
        full_ds, learning_rate=LEARNING_RATE, hidden_size=32, attention_head_size=2,
        dropout=0.1, hidden_continuous_size=16, output_size=[7] * len(C.TARGETS),
        loss=MultiLoss([QuantileLoss() for _ in C.TARGETS]), log_interval=-1,
        reduce_on_plateau_patience=3,
    )
    print(f"parâmetros: {tft.size() / 1e3:.1f}k")

    ckpt_dir = f"models/checkpoints/{tag}"
    shutil.rmtree(ckpt_dir, ignore_errors=True)
    ckpt = ModelCheckpoint(dirpath=ckpt_dir, filename="best", monitor="val_loss", mode="min", save_top_k=1)
    trainer = pl.Trainer(
        max_epochs=MAX_EPOCHS, accelerator="gpu" if torch.cuda.is_available() else "cpu", devices=1,
        precision="bf16-mixed" if torch.cuda.is_available() else 32,
        limit_train_batches=TRAIN_BATCHES_PER_EPOCH, gradient_clip_val=GRADIENT_CLIP_VAL,
        callbacks=[EarlyStopping(monitor="val_loss", min_delta=1e-4, patience=int(os.getenv("PATIENCE", "4")), mode="min"),
                   ckpt, LearningRateMonitor()],
        logger=TensorBoardLogger("models/logs", name=tag), enable_progress_bar=False,
    )
    trainer.fit(tft, train_dataloaders=train_dl, val_dataloaders=val_dl)
    print(f"melhor checkpoint: {ckpt.best_model_path} (val_loss={float(ckpt.best_model_score):.4f})")
    return ckpt.best_model_path


def main():
    tags = sys.argv[1:] or ["final"]
    if tags == ["all"]:
        tags = list(C.CUTS)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    base = C.load_base()
    for tag in tags:
        train_cut(tag, base)


if __name__ == "__main__":
    main()
