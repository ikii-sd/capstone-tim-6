# Validasi Artefak Baseline — Backlog #8

**Tanggal pemeriksaan:** 28 November 2026

**Model:** MFCC mean/std + Random Forest

**Dataset:** Data primer sesi-20261113-200606

**Status validasi lokal:** PASS

## Hasil Pemeriksaan

| Pemeriksaan | Hasil |
|---|---|
| Struktur metrics.json | Valid |
| Data hash manifest | ffcb1966eec8bf6b285607a0e19e97c0 |
| Data hash evaluator | ffcb1966eec8bf6b285607a0e19e97c0 |
| Data hash metrics.json | ffcb1966eec8bf6b285607a0e19e97c0 |
| Parameter split | split:2026 |
| Validation Accuracy | 0.912037 |
| Validation MAE | 0.087963 |
| Validation Macro F1 | 0.895914 |
| Jumlah prediksi validasi | 432 |
| Jumlah prediksi test | 0 |
| Kesesuaian CSV sesi | Sesuai |
| Kebocoran antarulangan pada split protokol | Tidak ditemukan |

## Reproduksi Pemeriksaan

```bash
python -m src.baseline.validate_artifacts
```

Variabel lingkungan SESI harus mengarah ke folder dataset primer asli dan DATA_SINTETIS tidak boleh aktif.

## Artefak Pendukung

- [Metrics](metrics.json)
- [Prediksi validasi](pred_val.npy)
- [Laporan validasi](artifact_validation.json)
- [Script validasi](../../src/baseline/validate_artifacts.py)
- [Kode baseline](../../src/baseline/mfcc_rf.py)

## Kesimpulan

Hasil perhitungan ulang metrik sesuai dengan artefak baseline. Ketiga data_hash telah sesuai dengan mekanisme evaluator resmi. Accuracy sebesar 91,20% dan MAE sebesar 0,087963 digunakan sebagai acuan pembanding pada data validasi.

Pemeriksaan ini merupakan validasi lokal dan bukan hasil pemeriksaan resmi Workbench maupun evaluasi data test akhir.