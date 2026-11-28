# Ringkasan Pemeriksaan Backlog #14

**Capstone Deep Learning — Tim 6**  
**PIC:** Ahmad Rizqi (122450138)  
**Jalur:** Transfer Learning  
**Dataset:** sesi-20261113-200606

## 1. Tujuan pemeriksaan

Dokumen ini menghubungkan hasil `metrics.json`, konfigurasi eksperimen pada `run.json`, dan hash dataset pada `data/MANIFEST.json` agar pembimbing dapat memeriksa konsistensi eksperimen secara langsung.

## 2. Identitas eksperimen utama

- Experiment ID: `957ac563eaef`
- Model: `tl`
- Kode: `models/122450138/run.py`
- Epoch: 25
- Batch size: 64
- Learning rate: 0.001
- Weight decay: 0.01
- Dropout: 0.3
- Freeze blocks: 3
- Norm embedding: False
- Split seed: 2026
- Perangkat: NVIDIA GeForce GTX 1650

## 3. Hasil validasi

| Seed | Accuracy | Macro-F1 | MAE |
|---|---:|---:|---:|
| 1 | 0.942130 | 0.940936 | 0.057870 |
| 2 | 0.939815 | 0.941399 | 0.060185 |
| 3 | 0.962963 | 0.962599 | 0.037037 |
| Rata-rata | 0.948302 | 0.948312 | 0.051698 |
| Simpangan baku sampel | 0.012749 | 0.012376 | 0.012749 |

Hasil seed 1 menggunakan 432 sampel validasi. File `metrics.json` utama mencatat `n_test = 0`, sehingga metrik yang dilaporkan merupakan hasil validasi, bukan hasil data uji final.

MAE tersimpan pada `run.json` dan `tl_metrics.csv`, sedangkan Accuracy serta Macro-F1 terdapat pada `metrics.json`.

## 4. Pemeriksaan hash dataset

| Sumber | Nilai |
|---|---|
| `data/MANIFEST.json` | `ffcb1966eec8bf6b285607a0e19e97c0` |
| `metrics.json` utama | `ffcb1966eec8bf6b285607a0e19e97c0` |
| Konfigurasi `run.json` | `ffcb1966eec8bf6b285607a0e19e97c0` |
| Perhitungan evaluator pada validasi lokal 26 November | `ffcb1966eec8bf6b285607a0e19e97c0` |

Parameter hash: `split:2026`.

Hash identik pada sembilan arsip eksperimen yang diperiksa. Pemeriksaan lokal sebelumnya juga melaporkan kecocokan hasil perhitungan evaluator dengan manifest.

Cakupan identitas WAV masih memerlukan tindak lanjut Penjaga Data sebagaimana dicatat pada laporan validasi.

## 5. Peta bukti eksperimen

| Bukti | Lokasi repository |
|---|---|
| Hasil metrik utama | `results/122450138/metrics.json` |
| Konfigurasi utama seed 1 | `results/122450138/experiments/957ac563eaef/seed_1/run.json` |
| Metrik utama seed 1 | `results/122450138/experiments/957ac563eaef/seed_1/metrics.json` |
| Konfigurasi dan metrik seed 2 | `results/122450138/experiments/957ac563eaef/seed_2/` |
| Konfigurasi dan metrik seed 3 | `results/122450138/experiments/957ac563eaef/seed_3/` |
| Rekap sembilan eksperimen | `results/122450138/tl_metrics.csv` |
| Manifest dataset | `data/MANIFEST.json` |
| Validasi lokal | `results/122450138/artifact_validation.md` |
| Bukti checksum | `results/122450138/artifact_validation.json` |
| Skrip validasi | `models/122450138/validate_artifacts.py` |

## 6. Reproduksi pemeriksaan

Jalankan dari root repository:

```powershell
python models/122450138/validate_artifacts.py
```

Skrip validasi lokal melaporkan PASS pada 26 November 2026, menggunakan evaluator resmi. Status eksekusi ulang terbaru dan pemeriksaan Local Runner DSWorkbench perlu dilampirkan secara terpisah.

## 7. Kesimpulan

Dari hasil pemeriksaan lokal sebelumnya, metrik, konfigurasi eksperimen, identitas prediksi, dan hash manifest menunjukkan konsistensi untuk eksperimen Transfer Learning dengan ID `957ac563eaef`.

Eksperimen utama seed 1 menghasilkan Accuracy validasi 94,21%, Macro-F1 0,940936, dan MAE 0,057870. Rata-rata Accuracy tiga seed pada konfigurasi yang sama adalah 94,83%.

Validasi data uji final belum dilakukan. Dokumen ini merupakan ringkasan bukti validasi, bukan klaim kelulusan Local Runner atau persetujuan akhir pembimbing.
