
"""Kerangka run.py anggota untuk model Transformer.

Penggunaan:
    python models/123450110/run.py --seed 1
    python models/123450110/run.py --seed 1 --final
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch

# Lokasi root repository
AKAR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AKAR))

from src.protokol import data  # noqa: E402
from transformer import TransformerKlasifikasi  # noqa: E402


NIM = Path(__file__).resolve().parent.name
JALUR = "trf"

# Konfigurasi training
EPOCHS = 2
BATCH_SIZE = 32
LEARNING_RATE = 0.001
WEIGHT_DECAY = 0.01


def latih_dan_prediksi(
    seed: int,
    final: bool,
    rekaman: list[dict] | None = None,
    perangkat: str = "cpu",
) -> tuple[np.ndarray, np.ndarray | None]:
    """Latih Transformer dan hasilkan prediksi validasi/test."""

    torch.manual_seed(seed)
    np.random.seed(seed)

    # Tentukan perangkat komputasi
    device = torch.device(perangkat)

    # Memuat data resmi atau data simulasi
    if rekaman is None:
        Xtr, ytr, Xva, _, Xte, _ = data.muat()
    else:
        Xtr, ytr, Xva, _, Xte, _ = data.muat(rekaman=rekaman)

    if len(Xtr) == 0 or len(Xva) == 0:
        raise ValueError("Data training atau validasi kosong.")

    # Mempertahankan bentuk [N, 64, 101]
    def ke_tensor(X):
        return torch.as_tensor(
            np.asarray(X, dtype=np.float32),
            dtype=torch.float32,
        )

    X_train = ke_tensor(Xtr).to(device)
    y_train = torch.as_tensor(
        np.asarray(ytr),
        dtype=torch.long,
    ).to(device)

    X_validasi = ke_tensor(Xva).to(device)

    # Inisialisasi model Transformer
    model = TransformerKlasifikasi(
        n_mel=data.N_MEL,
        d_model=64,
        nhead=4,
        num_layers=2,
        num_classes=data.N_KELAS,
        max_seq_len=101,
        dropout=0.1,
    ).to(device)

    # Optimizer
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
    )

    # Training
    print(f"Memulai training Transformer pada {device}...")

    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0.0

        # Acak urutan sampel setiap epoch
        indeks = torch.randperm(len(X_train), device=device)

        for i in range(0, len(X_train), BATCH_SIZE):
            idx = indeks[i:i + BATCH_SIZE]

            xb = X_train[idx]
            yb = y_train[idx]

            optimizer.zero_grad()

            logits = model(xb)
            loss = torch.nn.functional.cross_entropy(logits, yb)

            loss.backward()
            optimizer.step()

            total_loss += loss.item() * len(idx)

        rata_loss = total_loss / len(X_train)

        print(
            f"Epoch {epoch + 1}/{EPOCHS} "
            f"- Loss: {rata_loss:.4f}"
        )

    # Prediksi
    model.eval()

    with torch.no_grad():
        pred_val = (
            model(X_validasi)
            .argmax(dim=1)
            .cpu()
            .numpy()
        )

        pred_test = None

        if final and Xte is not None:
            X_test = ke_tensor(Xte).to(device)

            pred_test = (
                model(X_test)
                .argmax(dim=1)
                .cpu()
                .numpy()
            )

    return pred_val, pred_test


def main():
    """Menjalankan training, menyimpan prediksi, dan evaluasi."""

    parser = argparse.ArgumentParser(
        description="Training model Transformer untuk Capstone Tim 6."
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=1,
        help="Seed eksperimen.",
    )

    parser.add_argument(
        "--final",
        action="store_true",
        help="Aktifkan prediksi data test.",
    )

    parser.add_argument(
        "--perangkat",
        type=str,
        default="cpu",
        choices=["cpu", "cuda"],
        help="Perangkat komputasi.",
    )

    args = parser.parse_args()

    if args.perangkat == "cuda" and not torch.cuda.is_available():
        parser.error("CUDA diminta, tetapi tidak tersedia.")

    # Folder hasil
    folder_hasil = AKAR / "results" / NIM
    folder_hasil.mkdir(parents=True, exist_ok=True)

    # Mulai pencatatan waktu
    mulai = time.perf_counter()

    print("=" * 55)
    print("CAPSTONE TIM 6 - TRANSFORMER")
    print(f"NIM       : {NIM}")
    print(f"Seed      : {args.seed}")
    print(f"Final     : {args.final}")
    print(f"Perangkat : {args.perangkat}")
    print("=" * 55)

    # Training dan prediksi
    pred_val, pred_test = latih_dan_prediksi(
        seed=args.seed,
        final=args.final,
        perangkat=args.perangkat,
    )

    # Simpan prediksi validasi
    np.save(folder_hasil / "pred_val.npy", pred_val)

    print(f"Prediksi validasi disimpan: {pred_val.shape}")

    # Simpan prediksi test jika mode final
    if args.final and pred_test is not None:
        np.save(folder_hasil / "pred_test.npy", pred_test)
        print(f"Prediksi test disimpan: {pred_test.shape}")

    durasi = time.perf_counter() - mulai
    print(f"Durasi training dan prediksi: {durasi:.2f} detik")

        # Jalankan evaluator repository
    perintah = [
        sys.executable,
        "-m",
        "src.common.evaluate",
        "--nim",
        NIM,
        "--model",
        JALUR,
        "--seed",
        str(args.seed),
        "--pred-val",
        str(folder_hasil / "pred_val.npy"),
        "--durasi",
        str(durasi),
        "--perangkat",
        args.perangkat,
    ]

    if args.final:
        perintah.extend([
            "--pred-test",
            str(folder_hasil / "pred_test.npy"),
        ])

    print("\nMenjalankan evaluator...")

    subprocess.run(
        perintah,
        cwd=AKAR,
        check=True,
    )

    print("\nProses Transformer selesai.")