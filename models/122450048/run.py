"""CNN 2D (jalur cnn): taksiran jumlah alat bersuara (0..3) dari log-mel 64 x 101.

    python models/122450048/run.py --seed 1 [--final]

Hiperparameter bisa diubah lewat opsi (untuk tuning dan ablation), misalnya:
    python models/122450048/run.py --seed 1 --dropout 0 --wd 0
"""
# Model milik 122450048 (David Boby C. Nainggolan)
from __future__ import annotations

import argparse
import copy
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

AKAR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AKAR))
from src.protokol import data  # noqa: E402  (protokol tim yang dibekukan)

NIM = Path(__file__).resolve().parent.name     # nama folder = NIM
JALUR = "cnn"                                   # cnn | tl | rnn | trf | ae
N_KELAS = 4                                     # jumlah alat bersuara: 0, 1, 2, 3


def bangun_model(torch, dropout: float, pakai_bn: bool):
    """Masukan (B, 1, 64, 101) -> logit (B, 4)."""
    nn = torch.nn

    def blok(masuk: int, keluar: int):
        lapis = [nn.Conv2d(masuk, keluar, kernel_size=3, padding=1)]
        if pakai_bn:
            lapis.append(nn.BatchNorm2d(keluar))
        lapis += [nn.ReLU(), nn.MaxPool2d(2)]
        return nn.Sequential(*lapis)

    return nn.Sequential(
        blok(1, 16), blok(16, 32), blok(32, 64),   # (64, 101) -> (8, 12)
        nn.AdaptiveAvgPool2d((4, 1)),               # rata-rata waktu, pertahankan 4 zona frekuensi
        nn.Flatten(),                               # 64 * 4 = 256
        nn.Dropout(dropout),                        # regularisasi
        nn.Linear(64 * 4, N_KELAS),
    )


def prediksi(torch, model, X, batch: int = 256) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        return np.concatenate([model(X[i:i + batch]).argmax(1).numpy() for i in range(0, len(X), batch)])


def latih_dan_prediksi(seed: int, final: bool, hp: argparse.Namespace) -> tuple[np.ndarray, np.ndarray | None]:
    """Kembalikan (pred_val, pred_test|None)."""
    import torch
    import torch.nn.functional as F

    torch.manual_seed(seed)
    np.random.seed(seed)
    Xtr, ytr, Xva, yva, Xte, _ = data.muat()

    def ke_tensor(X):
        return torch.from_numpy(np.asarray(X, dtype=np.float32))[:, None]   # (N, 1, 64, 101)

    X, y = ke_tensor(Xtr), torch.from_numpy(np.asarray(ytr, dtype=np.int64))
    Xv, yv = ke_tensor(Xva), np.asarray(yva)
    print(f"X latih {tuple(X.shape)}, X val {tuple(Xv.shape)}, kelas {np.bincount(ytr, minlength=N_KELAS).tolist()}",
          flush=True)

    model = bangun_model(torch, hp.dropout, not hp.tanpa_bn)
    opt = torch.optim.AdamW(model.parameters(), lr=hp.lr, weight_decay=hp.wd)

    terbaik, state = -1.0, None
    for epoch in range(hp.epoch):
        model.train()
        urut = torch.randperm(len(X))
        total = 0.0
        for i in range(0, len(X), hp.batch):
            idx = urut[i:i + hp.batch]
            opt.zero_grad()
            loss = F.cross_entropy(model(X[idx]), y[idx])
            loss.backward()
            opt.step()
            total += loss.item() * len(idx)
        acc = float((prediksi(torch, model, Xv) == yv).mean())
        print(f"epoch {epoch + 1}/{hp.epoch}  loss {total / len(X):.4f}  val_acc {acc:.4f}", flush=True)
        if acc > terbaik:
            terbaik, state = acc, copy.deepcopy(model.state_dict())

    model.load_state_dict(state)               # pakai epoch dengan val_acc terbaik
    pred_val = prediksi(torch, model, Xv)
    pred_test = prediksi(torch, model, ke_tensor(Xte)) if final and Xte is not None else None
    return pred_val, pred_test


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--final", action="store_true", help="sprint terakhir: evaluasi data uji sekali")
    ap.add_argument("--perangkat", default="cpu laptop")
    ap.add_argument("--epoch", type=int, default=12)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--wd", type=float, default=1e-4, help="weight decay AdamW")
    ap.add_argument("--dropout", type=float, default=0.3)
    ap.add_argument("--tanpa-bn", action="store_true", help="ablation: tanpa BatchNorm")
    a = ap.parse_args()
    t0 = time.time()
    pred_val, pred_test = latih_dan_prediksi(a.seed, a.final, a)
    durasi = time.time() - t0
    out = AKAR / "results" / NIM
    out.mkdir(parents=True, exist_ok=True)
    np.save(out / "pred_val.npy", np.asarray(pred_val))
    perintah = [sys.executable, "-m", "src.common.evaluate", "--nim", NIM, "--model", JALUR, "--seed", str(a.seed),
                "--pred-val", str(out / "pred_val.npy"), "--durasi", f"{durasi:.1f}", "--perangkat", a.perangkat]
    if pred_test is not None:
        np.save(out / "pred_test.npy", np.asarray(pred_test))
        perintah += ["--pred-test", str(out / "pred_test.npy")]
    subprocess.run(perintah, check=True, cwd=AKAR)


if __name__ == "__main__":
    main()