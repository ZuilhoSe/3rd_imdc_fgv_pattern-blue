"""Pattern Blue v4 — treino: o mesmo de train_v3, com a configuração de common_v4. Uso: python train_v4.py final test4 ..."""
import common_v4 as W  # noqa: F401  (aplica a configuração v4 antes de importar o treino)
import train_v3 as T

W.configure_training(T)

if __name__ == "__main__":
    T.main()
