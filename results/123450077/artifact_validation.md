# Validasi Artefak Autoencoder — Backlog #18

## Identitas

- Nama: Wan Nashwa Alhasni Yuska
- NIM: 123450077
- Akun Git: nshaysk
- Model: Autoencoder (AE)
- Seed: 1
- Dataset: sesi-20261113-200606

## Hasil validasi

Status pemeriksaan lokal: **PASS**

| Pemeriksaan | Hasil |
|---|---|
| Accuracy | 0,738426 |
| MAE | 0,261574 |
| Macro F1 | 0,775304 |
| Jumlah data validasi | 432 |
| Jumlah data pengujian | 0 |
| Kesesuaian data_hash | PASS |
| Kesesuaian CSV sesi | PASS |
| Pemisahan ulangan | PASS |

Data hash manifest, evaluator, dan metrics.json:

`ffcb1966eec8bf6b285607a0e19e97c0`

## Perbandingan dengan baseline non-DL

| Metrik | Autoencoder | Random Forest |
|---|---:|---:|
| Accuracy | 73,84% | 91,20% |
| MAE | 0,261574 | 0,087963 |
| Macro F1 | 77,53% | 89,59% |

Performa AE masih berada di bawah baseline Random Forest. Eksperimen tiga seed dan tuning dilanjutkan pada Sprint 2.

## Bukti kontribusi

- Commit `927c58a`: Training AE data primer seed 1.
- Commit `3a43564`: Implementasi AE runner.
- Commit `9fabdfa`: Perubahan jalur model.
- Commit `8d22558`: Setup folder model.
- Pengajuan merge: https://github.com/ikii-sd/capstone-tim-6/pull/25

Keempat commit tercatat atas author Git `nshaysk`, sesuai konfigurasi Git anggota penanggung jawab.

## Reproduksi validasi

`python -m models.123450077.validate_artifacts`

Bukti pemeriksaan tersedia pada `results/123450077/artifact_validation.json`.

Validasi dilakukan terhadap artefak pelatihan seed 1 yang sudah tersedia tanpa training ulang. Perubahan runner berupa penambahan MAE otomatis telah lolos pemeriksaan sintaks, tetapi belum diuji melalui pelatihan ulang.