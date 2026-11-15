"""
Pattern Blue v3 — treino em duas etapas, um modelo por corte.

  1. Treino até a convergência: alvos <= Y-2, parada antecipada na temporada Y-1 -> best.ckpt
  2. Ajuste fino com todos os dados do corte: alvos <= Y-1, taxa menor e épocas fixas -> full.ckpt
     (a etapa 1 deixa a temporada mais recente fora do treino, e ela é justamente a mais informativa)

Uso (a partir de src/):  python train_v3.py test4 test3 ... final cut2021 ...
Retoma sozinho: pula o corte se full.ckpt já existe.
"""
import os
import shutil
import sys
import time
import warnings
import lightning.pytorch as pl
import torch
from lightning.pytorch.callbacks import EarlyStopping, LearningRateMonitor, ModelCheckpoint
from lightning.pytorch.loggers import TensorBoardLogger
from pytorch_forecasting import TemporalFusionTransformer

import common as C
import common_v3 as V

torch.set_float32_matmul_precision("medium")
warnings.filterwarnings("ignore")

BATCH_SIZE = int(os.getenv("BATCH_SIZE", "256"))
BATCHES_PER_EPOCH = int(os.getenv("BATCHES_PER_EPOCH", "400"))
MAX_EPOCHS = int(os.getenv("MAX_EPOCHS", "30"))
PATIENCE = int(os.getenv("PATIENCE", "6"))
LEARNING_RATE = 0.003
GRADIENT_CLIP_VAL = 0.1
FULL_EPOCHS = int(os.getenv("FULL_EPOCHS", "3"))
FULL_LR = 0.0003
NUM_WORKERS = int(os.getenv("NUM_WORKERS", "0"))


def trainer_args():
    gpu = torch.cuda.is_available()
    return dict(accelerator="gpu" if gpu else "cpu", devices=1, precision="bf16-mixed" if gpu else 32,
                limit_train_batches=BATCHES_PER_EPOCH, gradient_clip_val=GRADIENT_CLIP_VAL,
                enable_progress_bar=False, num_sanity_val_steps=0)


def loader(ds, train, batch_size):
    extra = dict(persistent_workers=True) if NUM_WORKERS else {}
    return ds.to_dataloader(train=train, batch_size=batch_size, num_workers=NUM_WORKERS, **extra)


def train_cut(tag, base):
    year = C.cut_year(tag)
    ckpt_dir = f"{V.CKPT_ROOT}/{tag}"
    if os.path.exists(f"{ckpt_dir}/full.ckpt"):
        print(f"{tag}: já treinado", flush=True)
        return
    t0 = time.time()
    pl.seed_everything(C.tag_seed(tag))
    print(f"\n==================== {tag}: corte EW{C.CUT_WEEK}/{year} ====================", flush=True)
    frame, tgt = V.build_training_frame(base, year)
    norm = C.fit_normalizer(tgt)
    real = frame[frame["date"] <= C.cut_date(year)]
    full_ds = V.build_dataset(real, norm)
    train_ds = full_ds.filter(lambda d: C.decoder_mask(d, real, C.TRAIN_DECODER_WEEKS, range(2000, year - 1)))
    val_ds = full_ds.filter(lambda d: C.decoder_mask(d, real, [C.VAL_DECODER_WEEK], [year - 1]))
    all_ds = full_ds.filter(lambda d: C.decoder_mask(d, real, C.TRAIN_DECODER_WEEKS, range(2000, year)))
    print(f"amostras: treino {len(train_ds)} | validação {len(val_ds)} | todos os dados {len(all_ds)} "
          f"| ajustes no corte {tgt['has_fit'].mean():.3f} | montagem {time.time() - t0:.0f}s", flush=True)
    val_dl = loader(val_ds, False, BATCH_SIZE * 4)

    tft = TemporalFusionTransformer.from_dataset(
        full_ds, learning_rate=LEARNING_RATE, hidden_size=32, attention_head_size=2, dropout=0.1,
        hidden_continuous_size=16, output_size=[7] * len(C.TARGETS), loss=V.make_loss(), log_interval=-1,
        reduce_on_plateau_patience=3)
    print(f"parâmetros: {tft.size() / 1e3:.1f}k", flush=True)

    shutil.rmtree(ckpt_dir, ignore_errors=True)
    ckpt = ModelCheckpoint(dirpath=ckpt_dir, filename="best", monitor="val_loss", mode="min", save_top_k=1)
    trainer = pl.Trainer(max_epochs=MAX_EPOCHS, logger=TensorBoardLogger(V.LOG_ROOT, name=tag),
                         callbacks=[EarlyStopping(monitor="val_loss", min_delta=1e-4, patience=PATIENCE, mode="min"),
                                    ckpt, LearningRateMonitor()], **trainer_args())
    t1 = time.time()
    trainer.fit(tft, train_dataloaders=loader(train_ds, True, BATCH_SIZE), val_dataloaders=val_dl)
    print(f"etapa 1: {trainer.current_epoch} épocas em {(time.time() - t1) / 60:.1f} min | "
          f"melhor val_loss={float(ckpt.best_model_score):.4f} | {os.path.basename(ckpt.best_model_path)}", flush=True)

    # etapa 2: sem validação independente; a escolha de épocas e taxa foi fixada antes de ver qualquer teste
    model = TemporalFusionTransformer.load_from_checkpoint(ckpt.best_model_path)
    model.configure_optimizers = lambda: torch.optim.Adam(model.parameters(), lr=FULL_LR)
    t2 = time.time()
    fine = pl.Trainer(max_epochs=FULL_EPOCHS, logger=TensorBoardLogger(V.LOG_ROOT, name=f"{tag}_full"),
                      enable_checkpointing=False, limit_val_batches=0, **trainer_args())
    fine.fit(model, train_dataloaders=loader(all_ds, True, BATCH_SIZE))
    fine.save_checkpoint(f"{ckpt_dir}/full.ckpt")
    print(f"etapa 2: {FULL_EPOCHS} épocas em {(time.time() - t2) / 60:.1f} min | total {(time.time() - t0) / 60:.1f} min", flush=True)
    del frame, real, full_ds, train_ds, val_ds, all_ds, tft, model, trainer, fine
    torch.cuda.empty_cache()


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    base = V.load_base()
    for tag in sys.argv[1:]:
        train_cut(tag, base)


if __name__ == "__main__":
    main()
