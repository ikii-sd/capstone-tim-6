"""Validasi lokal artefak TL dan telusur ringkasan tiga seed.

    python models/122450138/validate_artifacts.py

Laporan lokal ini dapat dilampirkan bersama hasil Periksa artefak DSWorkbench.
"""
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

import numpy as np

AKAR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AKAR))
from src.common import evaluate, manifest, split
from src.protokol import data


def periksa(kondisi, pesan):
    if not kondisi:
        raise ValueError(pesan)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    folder = AKAR / "results" / "122450138"
    path_metrics = folder / "metrics.json"
    path_pred = folder / "pred_val.npy"
    hasil = json.loads(path_metrics.read_text("utf-8"))
    m = manifest.baca()
    expected = manifest.data_hash(f"split:{split.SEED_SPLIT}".encode())
    periksa(m.get("data_hash") == expected == hasil.get("data_hash"),
            "Hash manifest, evaluator, dan metrics.json belum sama")
    periksa(bool(re.fullmatch(r"[0-9a-f]{32}", expected)), "Format hash tidak sesuai")
    periksa(type(hasil.get("seed")) is int and hasil["seed"] == 1, "Artefak utama harus seed 1")
    periksa(hasil.get("model") == "tl", "Jalur model harus tl")
    periksa(hasil.get("n_test") == 0, "Validasi ini ditujukan untuk artefak validasi")
    for key in ("val_acc", "val_macro_f1"):
        value = hasil.get("metrik", {}).get(key)
        periksa(type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1,
                f"Metrik {key} tidak sesuai skema")
    durasi = hasil.get("durasi_detik")
    periksa(type(durasi) in (int, float) and math.isfinite(durasi) and durasi >= 0,
            "Durasi harus angka hingga dan tidak negatif")
    periksa(isinstance(hasil.get("perangkat"), str) and bool(hasil["perangkat"]), "Perangkat kosong")
    # Gunakan penilai resmi untuk memeriksa ulang angka artefak utama.
    ulang, ukuran = evaluate.nilai(str(path_pred))
    periksa(hasil["n_val"] == ukuran["n_val"], "Ukuran validasi berbeda")
    periksa(all(hasil["metrik"][k] == round(v, 6) for k, v in ulang.items()),
            "Metrik utama berbeda dari hasil evaluator")
    _, _, _, y, _, _ = data.muat()
    pred_utama = np.load(path_pred, allow_pickle=False)
    configs = []
    for path in sorted((folder / "experiments").glob("*/seed_1/run.json")):
        info = json.loads(path.read_text("utf-8"))
        if path_pred.read_bytes() == path.with_name("pred_val.npy").read_bytes():
            if hasil == json.loads(path.with_name("metrics.json").read_text("utf-8")):
                configs.append(path)
    periksa(len(configs) == 1, "Artefak utama harus menunjuk tepat satu arsip seed 1")
    path_run = configs[0]
    acuan = json.loads(path_run.read_text("utf-8"))["konfigurasi"]
    kolom = ("freeze_blocks", "epoch", "batch", "lr", "wd", "dropout", "norm_emb", "data_hash")
    with (folder / "tl_metrics.csv").open(newline="", encoding="utf-8") as f:
        csv_rows = list(csv.DictReader(f))
    daftar = []
    for seed in (1, 2, 3):
        path = path_run.parent.parent / f"seed_{seed}"
        meta = json.loads((path / "run.json").read_text("utf-8"))
        config = meta["konfigurasi"]
        nilai = json.loads((path / "metrics.json").read_text("utf-8"))
        pred = np.load(path / "pred_val.npy", allow_pickle=False)
        periksa(all(config[k] == acuan[k] for k in kolom), "Konfigurasi antar-seed berbeda")
        periksa(config["seed"] == str(seed) and nilai["seed"] == seed, "Seed arsip tidak sesuai")
        periksa(config["data_hash"] == nilai["data_hash"] == expected, "Hash arsip tidak sesuai")
        periksa(pred.shape == y.shape and pred.dtype.kind in "iu" and np.isin(pred, range(4)).all(),
                "Prediksi harus label integer 0–3 dan panjang sesuai validasi")
        metrik = evaluate.metrik_klasifikasi(y, pred)
        periksa(all(nilai["metrik"][f"val_{k}"] == round(v, 6) for k, v in metrik.items()),
                "Metrik arsip tidak cocok dengan prediksi")
        mae = float(np.abs(y - pred).mean())
        periksa(np.isclose(mae, meta["val_mae"], atol=1e-12, rtol=0), "MAE arsip berbeda")
        rows = [r for r in csv_rows if r["seed"] == str(seed) and all(r[k] == config[k] for k in kolom)]
        periksa(len(rows) == 1, "Baris CSV konfigurasi ini tidak unik")
        periksa(all(float(rows[0][f"val_{k}"]) == nilai["metrik"][f"val_{k}"] for k in ("acc", "macro_f1")),
                "CSV berbeda dari metrics.json")
        periksa(abs(float(rows[0]["val_mae"]) - mae) < 1e-6, "MAE CSV berbeda")
        daftar.append({"seed": seed, "arsip": str(path.relative_to(AKAR)).replace("\\", "/"),
                       "val_acc": metrik["acc"], "val_macro_f1": metrik["macro_f1"], "val_mae": mae,
                       "pred_sha256": sha256(path / "pred_val.npy"),
                       "metrics_sha256": sha256(path / "metrics.json"),
                       "run_sha256": sha256(path / "run.json")})
    summary = {k: {"mean": float(np.mean([r[k] for r in daftar])),
                   "std_sample": float(np.std([r[k] for r in daftar], ddof=1))}
               for k in ("val_acc", "val_macro_f1", "val_mae")}
    commit = subprocess.run(["git", "-c", f"safe.directory={AKAR.as_posix()}", "-C", str(AKAR),
                             "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    report = {"status": "PASS", "jenis": "validasi lokal memakai evaluator resmi; bukan status Local Runner",
              "waktu_wib": datetime.now(timezone(timedelta(hours=7))).isoformat(), "head_saat_validasi": commit,
              "manifest_sha256": sha256(manifest.MANIFEST), "manifest_data_hash": m["data_hash"],
              "computed_evaluator_hash": expected, "metrics_data_hash": hasil["data_hash"],
              "parameter_hash": f"split:{split.SEED_SPLIT}", "berkas_manifest": m["berkas"],
              "metrics_sha256": sha256(path_metrics), "pred_sha256": sha256(path_pred),
              "metrics": hasil, "konfigurasi": acuan, "runs": daftar, "ringkasan_tiga_seed": summary}
    path_report = folder / "artifact_validation.json"
    path_report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("PASS validasi lokal metrics.json, prediksi, tiga hash yang sama, dan telusur konfigurasi")
    print("DATA_HASH", expected)
    print("KONFIGURASI", json.dumps(acuan))
    print("RINGKASAN_3_SEED", json.dumps(summary))
    print("LAPORAN", path_report)


if __name__ == "__main__":
    main()
