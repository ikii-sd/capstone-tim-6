
from pathlib import Path
import argparse
import time
import random
import sys

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.protokol import data
from transformer import TransformerKlasifikasi


# IDENTITAS MODEL
NIM = Path(__file__).resolve().parent.name
JALUR = "trf"


# KONFIGURASI TRAINING
EPOCHS = 2
BATCH_SIZE = 32
LEARNING_RATE = 0.001
WEIGHT_DECAY = 0.01
N_KELAS = 4
N_FOLD = 3


# UTILITAS
def atur_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def ke_tensor(X, y=None):
    X_tensor = torch.as_tensor(X, dtype=torch.float32)

    if y is None:
        return X_tensor

    y_tensor = torch.as_tensor(y, dtype=torch.long)
    return X_tensor, y_tensor


# TRAINING DAN PREDIKSI
def latih_dan_prediksi(seed, fold=0, final=False, perangkat="cpu"):
    atur_seed(seed)

    device = torch.device(perangkat)

    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA tidak tersedia pada perangkat ini.")

    print("\nMemuat dataset asli...")

    Xtr, ytr, Xva, yva, Xte, yte = data.muat(lipatan=fold)

    print(f"Fold     : {fold}")
    print(f"Training : {Xtr.shape} | {ytr.shape}")
    print(f"Validasi : {Xva.shape} | {yva.shape}")
    print(f"Pengujian: {Xte.shape} | {yte.shape}")

    if len(Xtr) == 0 or len(Xva) == 0:
        raise ValueError("Data training atau validasi kosong.")

    if Xtr.ndim != 3 or Xtr.shape[1:] != (64, 101):
        raise ValueError(
            f"Bentuk fitur tidak sesuai. Diharapkan (N,64,101), "
            f"didapatkan {Xtr.shape}"
        )

    X_train, y_train = ke_tensor(Xtr, ytr)
    X_validasi = ke_tensor(Xva)

    dataset = TensorDataset(X_train, y_train)

    generator = torch.Generator()
    generator.manual_seed(seed)

    loader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        generator=generator
    )

    model = TransformerKlasifikasi().to(device)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY
    )

    print(f"\nMemulai training Transformer pada {device}...")

    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0.0

        for xb, yb in loader:
            xb = xb.to(device)
            yb = yb.to(device)

            optimizer.zero_grad()

            logits = model(xb)

            if logits.ndim != 2 or logits.shape[1] != N_KELAS:
                raise ValueError(
                    f"Output model harus [batch,4], "
                    f"didapatkan {logits.shape}"
                )

            loss = torch.nn.functional.cross_entropy(logits, yb)

            loss.backward()
            optimizer.step()

            total_loss += loss.item() * len(xb)

        rata_loss = total_loss / len(dataset)

        print(
            f"Epoch {epoch + 1}/{EPOCHS} "
            f"- Loss: {rata_loss:.4f}"
        )

    # PREDIKSI VALIDASI
    model.eval()
    X_validasi = X_validasi.to(device)

    with torch.no_grad():
        pred_val = (
            model(X_validasi)
            .argmax(dim=1)
            .cpu()
            .numpy()
        )

    # PREDIKSI TEST HANYA PADA TAHAP FINAL
    pred_test = None

    if final:
        if Xte is None or len(Xte) == 0:
            raise ValueError("Data pengujian kosong.")

        X_test = ke_tensor(Xte).to(device)

        with torch.no_grad():
            pred_test = (
                model(X_test)
                .argmax(dim=1)
                .cpu()
                .numpy()
            )

    return pred_val, pred_test, model


# MAIN
def main():
    parser = argparse.ArgumentParser(
        description="Training Transformer - Capstone Tim 6"
    )

    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument(
        "--fold",
        type=int,
        choices=[0, 1, 2],
        default=0
    )
    parser.add_argument("--final", action="store_true")
    parser.add_argument(
        "--perangkat",
        choices=["cpu", "cuda"],
        default="cpu"
    )

    args = parser.parse_args()

    print("=" * 55)
    print("CAPSTONE TIM 6 - TRANSFORMER")
    print("=" * 55)

    print(f"NIM       : {NIM}")
    print(f"Seed      : {args.seed}")
    print(f"Fold      : {args.fold}")
    print(f"Final     : {args.final}")
    print(f"Perangkat : {args.perangkat}")

    folder_hasil = Path("results") / NIM / f"fold_{args.fold}"
    folder_hasil.mkdir(parents=True, exist_ok=True)

    waktu_mulai = time.time()

    pred_val, pred_test, model = latih_dan_prediksi(
        seed=args.seed,
        fold=args.fold,
        final=args.final,
        perangkat=args.perangkat
    )

    path_val = folder_hasil / "pred_val.npy"
    np.save(path_val, pred_val)
    print(f"\nPrediksi validasi disimpan: {path_val} {pred_val.shape}")

    if pred_test is not None:
        path_test = folder_hasil / "pred_test.npy"
        np.save(path_test, pred_test)
        print(f"Prediksi pengujian disimpan: {path_test} {pred_test.shape}")

    path_model = folder_hasil / "model_transformer.pt"
    torch.save(model.state_dict(), path_model)
    print(f"Model disimpan: {path_model}")

    durasi = time.time() - waktu_mulai

    print(f"\nDurasi: {durasi:.2f} detik")
    print("\nTraining Transformer selesai.")
    print(
        "Catatan: evaluator resmi belum dijalankan; "
        "hasil ini belum merupakan evaluasi akhir."
    )


if __name__ == "__main__":
    main()
