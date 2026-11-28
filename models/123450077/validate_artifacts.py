"""Validasi lokal artefak Autoencoder."""

import hashlib
import json
import math
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np

from src.common import evaluate, manifest, split
from src.protokol import data


def periksa(kondisi, pesan):
    if not kondisi:
        raise ValueError(pesan)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    folder = manifest.AKAR / "results" / "123450077"
    path_metrics = folder / "metrics.json"
    path_pred = folder / "pred_val.npy"

    periksa(
        os.environ.get("DATA_SINTETIS") != "1",
        "Data sintetis tidak boleh digunakan"
    )

    hasil = json.loads(path_metrics.read_text(encoding="utf-8"))
    m = manifest.baca()

    # Verifikasi data_hash
    expected = manifest.data_hash(
        f"split:{split.SEED_SPLIT}".encode()
    )

    periksa(
        m["data_hash"] == expected == hasil["data_hash"],
        "Data hash tidak sesuai"
    )

    periksa(
        len(expected) == 32
        and all(c in "0123456789abcdef" for c in expected),
        "Format hash tidak valid"
    )

    # Verifikasi struktur metrics.json
    periksa(type(hasil["seed"]) is int and hasil["seed"] == 1, "Seed tidak valid")
    periksa(
        hasil["model"] == "ae",
        "Identitas model tidak sesuai"
    )
    periksa(
        isinstance(hasil["perangkat"], str)
        and bool(hasil["perangkat"].strip()),
        "Perangkat tidak valid"
    )
    periksa(
        math.isfinite(hasil["durasi_detik"])
        and hasil["durasi_detik"] >= 0,
        "Durasi tidak valid"
    )

    # Pastikan CSV sesi sama dengan CSV repository
    sesi = data._folder_sesi()

    for nama in m["berkas"]:
        asli = sesi / Path(nama).name
        lokal = manifest.AKAR / nama
        periksa(
            sha256(asli) == sha256(lokal),
            f"CSV sesi berbeda: {nama}"
        )

    # Muat label dari protokol resmi
    _, _, _, y_val, _, _ = data.muat()
    pred = np.load(path_pred, allow_pickle=False)

    periksa(
        pred.shape == y_val.shape,
        "Ukuran prediksi tidak sesuai"
    )
    periksa(
        pred.dtype.kind in "iu",
        "Prediksi harus integer"
    )
    periksa(
        np.isin(pred, range(4)).all(),
        "Label prediksi di luar kelas 0-3"
    )

    # Hitung ulang metrik
    ulang = evaluate.metrik_klasifikasi(y_val, pred)

    metrik = {
        "val_acc": round(float(ulang["acc"]), 6),
        "val_macro_f1": round(float(ulang["macro_f1"]), 6),
        "val_mae": round(
            float(np.abs(y_val - pred).mean()), 6
        )
    }

    for key, value in metrik.items():
        periksa(
            hasil["metrik"][key] == value,
            f"Metrik {key} tidak sesuai"
        )

    periksa(
        hasil["n_val"] == len(y_val),
        "Jumlah validasi tidak sesuai"
    )
    periksa(
        hasil["n_test"] == 0,
        "Artefak ini ditujukan untuk validasi"
    )

    # Verifikasi pemisahan ulangan
    latih, val, uji = data.bagi_ulangan(
        range(1, 13), seed=split.SEED_SPLIT
    )

    data.periksa_kebocoran(
        np.asarray(latih),
        np.asarray(val),
        np.asarray(uji)
    )

    # Simpan laporan validasi
    laporan = {
        "status": "PASS",
        "jenis": "Validasi lokal Autoencoder",
        "waktu_wib": datetime.now(
            timezone(timedelta(hours=7))
        ).isoformat(),
        "model": hasil["model"],
        "sesi": sesi.name,
        "manifest_data_hash": m["data_hash"],
        "computed_evaluator_hash": expected,
        "metrics_data_hash": hasil["data_hash"],
        "parameter_hash": f"split:{split.SEED_SPLIT}",
        "csv_sesi_sesuai_manifest": True,
        "metrics_sha256": sha256(path_metrics),
        "pred_sha256": sha256(path_pred),
        "metrik_tersimpan": hasil["metrik"],
        "metrik_hitung_ulang": metrik,
        "n_val": len(y_val),
        "n_test": hasil["n_test"],
        "kelas_prediksi": np.unique(pred).tolist(),
        "ulangan_latih": latih,
        "ulangan_validasi": val,
        "ulangan_uji": uji,
        "kebocoran_ulangan": False
    }

    output = folder / "artifact_validation.json"

    output.write_text(
        json.dumps(laporan, indent=2) + "\n",
        encoding="utf-8"
    )

    print("PASS: Validasi lokal artefak Autoencoder")
    print("DATA_HASH:", expected)
    print("ACCURACY:", metrik["val_acc"])
    print("MAE:", metrik["val_mae"])
    print("MACRO F1:", metrik["val_macro_f1"])
    print("N_VAL:", len(y_val))
    print("LAPORAN:", output)


if __name__ == "__main__":
    main()