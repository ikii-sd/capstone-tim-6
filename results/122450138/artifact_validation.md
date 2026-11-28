# Bukti validasi lokal artefak TL — Backlog 14

Status **PASS** pada 2026-11-26T09:20:40.355405+07:00.
Laporan ini dihasilkan `models/122450138/validate_artifacts.py` dengan memakai
fungsi evaluator resmi untuk menghitung ulang metrik. Hasil Periksa artefak
Local Runner DSWorkbench perlu dilampirkan setelah input validasi masuk commit.

## Kesesuaian hash

| Sumber | data_hash |
|---|---|
| Field manifest | `ffcb1966eec8bf6b285607a0e19e97c0` |
| Perhitungan evaluator dari berkas manifest dan split | `ffcb1966eec8bf6b285607a0e19e97c0` |
| metrics.json utama | `ffcb1966eec8bf6b285607a0e19e97c0` |

Hash dihitung dari isi tujuh CSV terdaftar, urut nama, lalu tambahan `split:2026`,
melalui `src.common.manifest.data_hash`. Hash CSV tanpa split tersimpan sebagai
`data_hash_tanpa_split` pada manifest. Cakupan identitas WAV masih perlu ditinjau
Penjaga Data sebagaimana catatan audit tim.

## Hasil seed 1 dan keterlacakan Log Sprint

Artefak utama memakai seed 1, konfigurasi `freeze_blocks=3`, `epoch=25`,
`batch=64`, `lr=0.001`, `wd=0.01`, `dropout=0.3`, dan normalisasi embedding identitas.
Split data tetap memakai seed 2026. Sebanyak 432 prediksi validasi berupa label
integer kelas 0–3 cocok dengan ukuran data. Akurasi dan macro-F1 sesuai hasil
penghitungan ulang evaluator. JSON utama cocok dengan arsip konfigurasi seed 1.

| Seed | Akurasi | Macro-F1 | MAE | Arsip |
|---:|---:|---:|---:|---|
| 1 | 0.942130 | 0.940936 | 0.057870 | `results/122450138/experiments/957ac563eaef/seed_1` |
| 2 | 0.939815 | 0.941399 | 0.060185 | `results/122450138/experiments/957ac563eaef/seed_2` |
| 3 | 0.962963 | 0.962599 | 0.037037 | `results/122450138/experiments/957ac563eaef/seed_3` |

Ringkasan tiga seed konfigurasi yang sama menghasilkan akurasi
94.83% ±
1.27 poin persentase,
macro-F1 0.948312 ±
0.012376, dan MAE
0.051698 ±
0.012749. Simpangan baku memakai
pembagi n−1. Ringkasan Log Sprint harus merujuk ketiga arsip tersebut.
Angka pada metrics.json utama merujuk seed 1.

## Memeriksa ulang

```powershell
python models/122450138/validate_artifacts.py
```

`artifact_validation.json` memuat checksum manifest, prediksi, metrik, dan
metadata konfigurasi serta referensi HEAD saat pemeriksaan. Setelah perubahan
di-commit dan di-push, jalankan Periksa artefak pada DSWorkbench dan lampirkan
hasilnya bersama tautan commit yang memuat manifest, artefak, serta bukti ini.
