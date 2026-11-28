
"""Autoencoder (AE) untuk klasifikasi audio - Tim 6.

Training data primer:
    python models/123450077/run.py --seed 1

Smoke test:
    python models/123450077/run.py --smoke-test
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

AKAR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AKAR))

from src.protokol import data
from src.common import evaluate

NIM = Path(__file__).resolve().parent.name
JALUR = "ae"

JUMLAH_KELAS = 4
JUMLAH_EPOCH = 20
BATCH_SIZE = 128
LEARNING_RATE = 0.001
WEIGHT_DECAY = 0.0001


# ============================================================
# MODEL AUTOENCODER
# ============================================================

def buat_model():
    import torch.nn as nn
    import torch.nn.functional as F

    class Autoencoder(nn.Module):
        def __init__(self):
            super().__init__()

            self.encoder = nn.Sequential(
                nn.Conv2d(
                    1, 16,
                    kernel_size=3,
                    stride=2,
                    padding=1
                ),
                nn.ReLU(),
                nn.Conv2d(
                    16, 32,
                    kernel_size=3,
                    stride=2,
                    padding=1
                ),
                nn.ReLU()
            )

            self.decoder = nn.Sequential(
                nn.ConvTranspose2d(
                    32, 16,
                    kernel_size=3,
                    stride=2,
                    padding=1,
                    output_padding=1
                ),
                nn.ReLU(),
                nn.ConvTranspose2d(
                    16, 1,
                    kernel_size=3,
                    stride=2,
                    padding=1,
                    output_padding=1
                )
            )

            self.classifier = nn.Sequential(
                nn.AdaptiveAvgPool2d((1, 1)),
                nn.Flatten(),
                nn.Linear(32, JUMLAH_KELAS)
            )

        def forward(self, x):
            encoded = self.encoder(x)

            reconstructed = self.decoder(encoded)

            reconstructed = F.interpolate(
                reconstructed,
                size=x.shape[-2:],
                mode="bilinear",
                align_corners=False
            )

            classification = self.classifier(encoded)

            return reconstructed, classification

    return Autoencoder()


# ============================================================
# KONVERSI DATA
# ============================================================

def ke_tensor(X):
    import torch

    X = torch.as_tensor(
        np.asarray(X),
        dtype=torch.float32
    )

    if X.ndim == 3:
        X = X.unsqueeze(1)

    elif X.ndim == 4 and X.shape[-1] == 1:
        X = X.permute(0, 3, 1, 2)

    if X.ndim != 4 or X.shape[1] != 1:
        raise ValueError(
            f"Bentuk input tidak sesuai: {tuple(X.shape)}"
        )

    return X


def ke_label(y):
    import torch

    y = torch.as_tensor(np.asarray(y))

    if y.ndim > 1:
        y = y.argmax(dim=1)

    return y.long().reshape(-1)


# ============================================================
# SMOKE TEST
# ============================================================

def smoke_test():
    import torch

    print("Menjalankan smoke test Autoencoder...")

    model = buat_model()

    X = torch.randn(2, 1, 64, 101)

    rekonstruksi, klasifikasi = model(X)

    print("Input:", X.shape)
    print("Rekonstruksi:", rekonstruksi.shape)
    print("Klasifikasi:", klasifikasi.shape)

    assert rekonstruksi.shape == X.shape
    assert klasifikasi.shape == (2, JUMLAH_KELAS)

    loss_ae = torch.nn.MSELoss()(rekonstruksi, X)

    label = torch.tensor([0, 1])

    loss_cls = torch.nn.CrossEntropyLoss()(
        klasifikasi,
        label
    )

    loss = loss_ae + loss_cls
    loss.backward()

    print("Loss:", loss.item())
    print("Smoke test berhasil!")


# ============================================================
# TRAINING DAN PREDIKSI
# ============================================================

def latih_dan_prediksi(seed: int):
    import torch
    import torch.nn as nn

    torch.manual_seed(seed)
    np.random.seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    print("Memuat data primer melalui src/protokol...")

    # Split resmi tim, tanpa mengubah seed split protokol.
    Xtr, ytr, Xva, _, _, _ = data.muat()

    X = ke_tensor(Xtr)
    y = ke_label(ytr)
    X_val = ke_tensor(Xva)

    if len(X) != len(y):
        raise ValueError(
            "Jumlah data dan label training tidak sama."
        )

    if len(X) == 0 or len(X_val) == 0:
        raise ValueError("Data training/validasi kosong.")

    print("Jumlah training:", len(X))
    print("Jumlah validasi:", len(X_val))

    model = buat_model()

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY
    )

    loss_rekonstruksi = nn.MSELoss()
    loss_klasifikasi = nn.CrossEntropyLoss()

    for epoch in range(JUMLAH_EPOCH):
        model.train()

        indeks = torch.randperm(len(X))

        total_loss = 0.0
        jumlah_batch = 0

        for i in range(0, len(X), BATCH_SIZE):
            idx = indeks[i:i + BATCH_SIZE]

            xb = X[idx]
            yb = y[idx]

            optimizer.zero_grad()

            rekonstruksi, klasifikasi = model(xb)

            loss_ae = loss_rekonstruksi(
                rekonstruksi,
                xb
            )

            loss_cls = loss_klasifikasi(
                klasifikasi,
                yb
            )

            loss = loss_ae + loss_cls

            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            jumlah_batch += 1

        rata_loss = total_loss / jumlah_batch

        print(
            f"Epoch {epoch + 1}/{JUMLAH_EPOCH} "
            f"- Loss: {rata_loss:.4f}",
            flush=True
        )

    # Evaluasi hanya pada data validasi.
    model.eval()

    with torch.no_grad():
        _, output_val = model(X_val)
        pred_val = output_val.argmax(dim=1).cpu().numpy()

    return pred_val


# ============================================================
# PROGRAM UTAMA
# ============================================================

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--seed",
        type=int,
        default=1
    )

    parser.add_argument(
        "--perangkat",
        default="cpu laptop"
    )

    parser.add_argument(
        "--smoke-test",
        action="store_true"
    )

    args = parser.parse_args()

    if args.smoke_test:
        smoke_test()
        return

    print("Menyiapkan data primer meja...")

    waktu_awal = time.time()

    pred_val = latih_dan_prediksi(args.seed)

    durasi = time.time() - waktu_awal

    print("Training selesai.")
    print("Jumlah prediksi validasi:", len(pred_val))

    output_dir = AKAR / "results" / NIM
    output_dir.mkdir(parents=True, exist_ok=True)

    file_val = output_dir / "pred_val.npy"
    np.save(file_val, pred_val)

    # Evaluasi resmi menggunakan hash MANIFEST asli.
    perintah = [
        "evaluate",
        "--nim", NIM,
        "--model", JALUR,
        "--seed", str(args.seed),
        "--pred-val", str(file_val),
        "--durasi", f"{durasi:.1f}",
        "--perangkat", args.perangkat
    ]

    argv_awal = sys.argv

    try:
        sys.argv = perintah
        evaluate.main()
    finally:
        sys.argv = argv_awal

    # Tambahkan MAE tanpa mengubah evaluator resmi tim.
    import json
    from src.protokol.data import muat

    _, _, _, y_val, _, _ = muat()

    y_val = np.asarray(y_val, dtype=np.int64)
    pred_val = np.asarray(pred_val, dtype=np.int64)

    assert y_val.shape == pred_val.shape

    val_mae = float(np.abs(y_val - pred_val).mean())

    file_metrics = output_dir / "metrics.json"

    metrics = json.loads(
        file_metrics.read_text(encoding="utf-8")
    )

    metrics["metrik"]["val_mae"] = round(val_mae, 6)

    file_metrics.write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    print("Validation MAE:", round(val_mae, 6))
    print("Proses run.py selesai!")


if __name__ == "__main__":
    main()
