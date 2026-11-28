
"""Baseline non-DL: MFCC mean/std + Random Forest."""

import argparse
import json
import os
import time
from pathlib import Path

import librosa
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, mean_absolute_error, f1_score

from src.common.manifest import data_hash
from src.common.split import SEED_SPLIT
from src.protokol import data as protokol


def ekstrak_fitur(jendela):
    """13 MFCC: mean + std = 26 fitur per jendela."""
    fitur = []
    for audio in jendela:
        mfcc = librosa.feature.mfcc(
            y=audio,
            sr=protokol.SR,
            n_mfcc=13,
            n_fft=protokol.N_FFT,
            hop_length=protokol.HOP,
            n_mels=protokol.N_MEL,
            fmin=protokol.FMIN,
            fmax=protokol.FMAX,
            htk=True,
        )
        fitur.append(
            np.concatenate([mfcc.mean(axis=1), mfcc.std(axis=1)])
        )
    return np.asarray(fitur, dtype=np.float32)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--sintetis", action="store_true")
    args = parser.parse_args()

    mulai = time.perf_counter()

    if args.sintetis:
        rekaman = protokol.rekaman_sintetis()
    else:
        if os.environ.get("DATA_SINTETIS") == "1":
            raise RuntimeError(
                "DATA_SINTETIS=1 aktif. Nonaktifkan untuk evaluasi primer."
            )
        rekaman = protokol._baca_sesi()

    X, y, grup = [], [], []

    for r in rekaman:
        jendela = protokol.potong(r["audio"])
        if len(jendela) == 0:
            continue

        X.append(ekstrak_fitur(jendela))
        y.extend([r["y"]] * len(jendela))
        grup.extend([r["ulangan"]] * len(jendela))

    X = np.concatenate(X)
    y = np.asarray(y, dtype=np.int64)
    grup = np.asarray(grup)

    latih, val, uji = protokol.bagi_ulangan(
        grup, seed=SEED_SPLIT
    )

    m_latih = np.isin(grup, latih)
    m_val = np.isin(grup, val)
    m_uji = np.isin(grup, uji)

    protokol.periksa_kebocoran(
        grup[m_latih], grup[m_val], grup[m_uji]
    )

    model = RandomForestClassifier(
        n_estimators=200,
        random_state=args.seed,
        n_jobs=-1,
    )
    model.fit(X[m_latih], y[m_latih])

    pred = model.predict(X[m_val])

    metrik = {
        "val_acc": round(float(accuracy_score(y[m_val], pred)), 6),
        "val_mae": round(float(mean_absolute_error(y[m_val], pred)), 6),
        "val_macro_f1": round(
            float(f1_score(y[m_val], pred, average="macro")), 6
        ),
    }

    hasil = {
        "metrik": metrik,
        "seed": args.seed,
        "data_hash": data_hash(f"split:{SEED_SPLIT}".encode()),
        "perangkat": "cpu laptop",
        "model": "mfcc_mean_std_random_forest",
        "n_val": int(m_val.sum()),
        "n_test": 0,
        "durasi_detik": round(time.perf_counter() - mulai, 1),
    }

    if args.sintetis:
        print("HASIL SIMULASI (bukan evaluasi resmi)")
        print(json.dumps(hasil, indent=2))
        return

    folder = Path("results/baseline")
    folder.mkdir(parents=True, exist_ok=True)

    (folder / "metrics.json").write_text(
        json.dumps(hasil, indent=2) + "\n",
        encoding="utf-8",
    )
    np.save(folder / "pred_val.npy", pred)

    print(json.dumps(hasil, indent=2))


if __name__ == "__main__":
    main()
