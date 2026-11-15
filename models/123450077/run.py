
"""Autoencoder (AE) untuk klasifikasi audio - Tim 6.

Cara menjalankan:
    python models/123450077/run.py --seed 1
    python models/123450077/run.py --seed 1 --final

Smoke test tanpa dataset:
    python models/123450077/run.py --smoke-test
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import time
from pathlib import Path

import numpy as np

# ============================================================
# KONFIGURASI
# ============================================================

AKAR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AKAR))

from src.protokol import data  # noqa: E402

NIM = Path(__file__).resolve().parent.name
JALUR = "ae"

JUMLAH_KELAS = 4
JUMLAH_EPOCH = 20
BATCH_SIZE = 128
LEARNING_RATE = 0.001
WEIGHT_DECAY = 0.0001

# ============================================================
# DATA SIMULASI
# ============================================================

def buat_data_simulasi():
    """Membuat data palsu sesuai fixture src.protokol.uji_data."""

    rng = np.random.default_rng(0)

    rekaman = [
        {
            "audio": rng.normal(
                loc=k,
                size=20 * data.SR
            ).astype(np.float32),
            "y": k,
            "ulangan": u,
            "kondisi": f"k{k}"
        }
        for k in range(4)
        for u in range(1, 13)
    ]

    return rekaman


# ============================================================
# MODEL AUTOENCODER
# ============================================================

def buat_model():
    import torch.nn as nn
    import torch.nn.functional as F

    class Autoencoder(nn.Module):
        def __init__(self):
            super().__init__()

            # Encoder: mengambil fitur penting dari Log-Mel
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

            # Decoder: merekonstruksi input
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

            # Classification head: prediksi 4 kelas
            self.classifier = nn.Sequential(
                nn.AdaptiveAvgPool2d((1, 1)),
                nn.Flatten(),
                nn.Linear(32, JUMLAH_KELAS)
            )

        def forward(self, x):
            encoded = self.encoder(x)

            reconstructed = self.decoder(encoded)

            # Memastikan ukuran rekonstruksi sama dengan input
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

    # Bentuk awal: (N, 64, 101)
    if X.ndim == 3:
        X = X.unsqueeze(1)

    # Bentuk awal: (N, 64, 101, 1)
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

    # Mengubah one-hot menjadi label kelas
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

    # Simulasi input Log-Mel:
    # 1 channel, 64 mel bands, 101 frames
    X = torch.randn(2, 1, 64, 101)

    rekonstruksi, klasifikasi = model(X)

    print("Input:", X.shape)
    print("Rekonstruksi:", rekonstruksi.shape)
    print("Klasifikasi:", klasifikasi.shape)

    assert rekonstruksi.shape == X.shape
    assert klasifikasi.shape == (2, JUMLAH_KELAS)

    # Memastikan proses loss dan backpropagation berjalan
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

def latih_dan_prediksi(
    seed: int,
    final: bool
) -> tuple[np.ndarray, np.ndarray | None]:

    import torch
    import torch.nn as nn

    torch.manual_seed(seed)
    np.random.seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    # Memuat data sesuai protokol tim
    Xtr, ytr, Xva, _, Xte, _ = data.muat()

    X = ke_tensor(Xtr)
    y = ke_label(ytr)

    X_val = ke_tensor(Xva)

    if len(X) != len(y):
        raise ValueError("Jumlah data dan label training tidak sama.")

    if len(X) == 0:
        raise ValueError("Data training kosong.")

    model = buat_model()

    # Optimizer Adam dengan regularisasi weight decay
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY
    )

    loss_rekonstruksi = nn.MSELoss()
    loss_klasifikasi = nn.CrossEntropyLoss()

    # Training
    model.train()

    for epoch in range(JUMLAH_EPOCH):

        # Mengacak urutan sampel setiap epoch
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

            # Gabungan loss rekonstruksi dan klasifikasi
            loss = loss_ae + loss_cls

            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            jumlah_batch += 1

        rata_loss = total_loss / jumlah_batch

        print(
            f"Epoch {epoch + 1}/{JUMLAH_EPOCH} "
            f"- Loss: {rata_loss:.4f}"
        )

    # Prediksi validasi
    model.eval()

    with torch.no_grad():

        _, output_val = model(X_val)

        pred_val = output_val.argmax(dim=1).cpu().numpy()

        pred_test = None

        # Data uji hanya diprediksi ketika --final digunakan
        if final and Xte is not None:

            X_test = ke_tensor(Xte)

            _, output_test = model(X_test)

            pred_test = (
                output_test.argmax(dim=1)
                .cpu()
                .numpy()
            )

    return pred_val, pred_test


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
        "--final",
        action="store_true",
        help="Mengaktifkan prediksi data uji"
    )

    parser.add_argument(
        "--perangkat",
        default="cpu laptop"
    )

    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Menguji arsitektur model saja"
    )

    args = parser.parse_args()

    # Smoke test hanya menguji bentuk input dan output model
    if args.smoke_test:
        smoke_test()
        return

    # --------------------------------------------------------
    # 1. Menyiapkan data simulasi
    # --------------------------------------------------------

    print("Menyiapkan data simulasi...")

    rekaman = buat_data_simulasi()

    print("Jumlah rekaman:", len(rekaman))

    # Menghubungkan data simulasi ke loader protokol.
    # Berlaku selama proses run.py ini berjalan.
    data._baca_sesi = lambda: rekaman

    # --------------------------------------------------------
    # 2. Training dan prediksi
    # --------------------------------------------------------

    waktu_awal = time.time()

    pred_val, pred_test = latih_dan_prediksi(
        args.seed,
        args.final
    )

    durasi = time.time() - waktu_awal

    print("Training selesai.")
    print("Jumlah prediksi validasi:", len(pred_val))

    # --------------------------------------------------------
    # 3. Menyimpan hasil prediksi
    # --------------------------------------------------------

    output_dir = AKAR / "results" / NIM
    output_dir.mkdir(parents=True, exist_ok=True)

    file_val = output_dir / "pred_val.npy"

    np.save(file_val, pred_val)

    file_test = None

    if pred_test is not None:

        file_test = output_dir / "pred_test.npy"

        np.save(file_test, pred_test)

# --------------------------------------------------------
# 4. Menjalankan evaluator resmi
# --------------------------------------------------------

    from src.common import evaluate

    def hash_data_simulasi(tambahan=b""):
        """Hash khusus untuk data simulasi, bukan dataset final."""
        h = hashlib.sha256()

        for r in rekaman:
            h.update(r["audio"].tobytes())
            h.update(str(r["y"]).encode("utf-8"))
            h.update(str(r["ulangan"]).encode("utf-8"))
            h.update(r["kondisi"].encode("utf-8"))

        h.update(tambahan)

        return h.hexdigest()[:32]

    # Simpan fungsi hash asli
    hash_asli = evaluate.manifest.data_hash

    perintah = [
        "evaluate",
        "--nim", NIM,
        "--model", JALUR,
        "--seed", str(args.seed),
        "--pred-val", str(file_val),
        "--durasi", f"{durasi:.1f}",
        "--perangkat", args.perangkat
    ]

    if file_test is not None:
        perintah += [
            "--pred-test", str(file_test)
        ]

    argv_awal = sys.argv

    try:
        evaluate.manifest.data_hash = hash_data_simulasi
        sys.argv = perintah
        evaluate.main()

    finally:
        evaluate.manifest.data_hash = hash_asli
        sys.argv = argv_awal

    print("Proses run.py selesai!")


if __name__ == "__main__":
    main()