# Catatan model 122450138 — Backlog #13 (Transfer Learning PANNs Cnn6)

Model menerima masukan log-mel ternormalisasi dari `src.protokol.data.muat()` dengan bentuk
`(N, 64, 101)` untuk jendela audio dua detik (16 kHz, 64 pita mel). *Backbone* pralatih
yang digunakan adalah **PANNs Cnn6** ([bobot resmi AudioSet](https://zenodo.org/records/3987831),
`Cnn6_mAP=0.343.pth`), diadaptasi agar menerima spektrogram log-mel tim secara langsung
tanpa *frontend* gelombang mentah bawaan PANNs.

Pada konfigurasi akhir (`--freeze-blocks 3`), lapisan awal-menengah (`bn0` dan `conv_block1`
hingga `conv_block3`) dibekukan untuk mempertahankan detektor fitur akustik dasar dari AudioSet
sekaligus memungkinkan ekstraksi fitur *stem* dilakukan cukup sekali per bagian (*split*).
Blok konvolusi tingkat tinggi (`conv_block4`, 256→512 kanal), lapisan proyeksi (`fc1`, 512→512),
serta *classifier head* (`TLClassifierHead`: `Linear(512, 128) -> ReLU -> Dropout(0.3) -> Linear(128, 4)`)
di-*fine-tune* bersama untuk memetakan representasi audio ke 4 kelas jumlah alat bersuara (0, 1, 2, 3).

## Alasan optimizer

**AdamW** (`lr=0.001`, `weight_decay=0.01`) dipilih karena pemisahan peluruhan bobot (*decoupled
weight decay*) menstabilkan proses *fine-tuning* lapisan pralatih (`conv_block4` dan `fc1`)
yang memiliki skala gradien berbeda dari *classifier head* yang diinisialisasi acak. Pemilihan
*checkpoint* terbaik didasarkan pada akurasi validasi tertinggi selama 25 epoch (`batch_size=64`).

## Regularisasi

1. **Pembekuan bertingkat (*partial backbone freezing*, `--freeze-blocks 3`):** membekukan
   `bn0` dan `conv_block1..3` mencegah *catastrophic forgetting* dan *overfitting* pada 3.024
   jendela latih (7 ulangan).
2. **Dropout (`p = 0.3`)** pada *classifier head* sebelum lapisan linier akhir.
3. **Decoupled Weight Decay (`wd = 0.01`)** pada AdamW.

## Pencarian hyperparameter (tabel)

Eksperimen dilakukan pada dataset meja asli `sesi-20261113-200606` (latih: 3.024 jendela,
validasi: 432 jendela, split per ulangan dengan seed 2026):

| Mode / Freeze | Epoch | Batch | LR | Weight Decay | Dropout | Norm Emb | val_acc (rerata 3 seed) | val_macro_f1 (rerata 3 seed) | val_mae | Durasi rata-rata |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| Beku penuh (`freeze=4`, awal Sprint 0) | 10 | 128 | 0.001 | 0.01 | 0.3 | Tidak | 0.7593 ± 0.0050 | 0.7970 ± 0.0048 | 0.2438 | 24 s |
| Beku penuh (`freeze=4`) + Norm Emb | 20 | 64 | 0.001 | 0.01 | 0.3 | Ya | 0.8410 ± 0.0039 | 0.8593 ± 0.0040 | 0.1651 | 25 s |
| Beku penuh (`freeze=4`) + Norm Emb | 40 | 64 | 0.001 | 0.01 | 0.3 | Ya | 0.8565 ± 0.0068 | 0.8723 ± 0.0049 | 0.1481 | 26 s |
| Beku penuh (`freeze=4`) + Norm Emb | 60 | 64 | 0.001 | 0.01 | 0.3 | Ya | 0.8634 ± 0.0068 | 0.8746 ± 0.0044 | 0.1420 | 28 s |
| Beku penuh (`freeze=4`) + Norm Emb | 40 | 64 | 0.003 | 0.01 | 0.3 | Ya | 0.8472 ± 0.0000 | 0.8619 ± 0.0027 | 0.1590 | 26 s |
| **Partial FT (`freeze=3`, konfigurasi akhir)** | **25** | **64** | **0.001** | **0.01** | **0.3** | **Ya** | **0.9483 ± 0.0058** | **0.9524 ± 0.0068** | **0.0517** | **82 s** |

## Ablation (>= 2)

1. **Ablasi 1 — Pembekuan penuh *backbone* (`--freeze-blocks 4`) vs *Partial Fine-Tuning* (`--freeze-blocks 3`):**
   Membekukan `conv_block4` dan `fc1` menurunkan `val_acc` dari **0.9483 ± 0.0058** menjadi
   **0.8248 ± 0.0011** (atau **0.8565 ± 0.0068** pada 40 epoch) dan menaikkan MAE dari **0.0517**
   menjadi **0.1481–0.1813**. Hal ini membuktikan bahwa adaptasi blok konvolusi terakhir (`conv_block4`)
   sangat penting karena distribusi log-mel tim dinormalisasi per pita (mean 0, std 1), berbeda
   dari skala desibel mentah saat PANNs dilatih pada AudioSet.
2. **Ablasi 2 — Tanpa regularisasi Dropout & Weight Decay (`--dropout 0.0 --wd 0.0`):**
   Menghilangkan dropout dan weight decay pada mode *partial fine-tuning* menurunkan kestabilan
   dan akurasi validasi rerata menjadi **0.9360 ± 0.0039** (`val_macro_f1` **0.9347 ± 0.0043**,
   MAE **0.0640**) dibanding konfigurasi penuh (**0.9483 ± 0.0058**).
3. **Ablasi 3 — Tanpa normalisasi embedding pada ekstraktor beku (`--freeze-blocks 4 --tanpa-norm-emb`):**
   Tanpa standarisasi *embedding* berbasis data latih, akurasi validasi turun dari **0.8410**
   menjadi **0.7593 ± 0.0050** karena magnitudo aktivasi ReLU keluaran `fc1` belum terpusat di nol.

## Hasil 3 seed konfigurasi akhir

Perintah reproduksi:

```powershell
python models/122450138/run.py --seed 1
python models/122450138/run.py --seed 2
python models/122450138/run.py --seed 3
```

| Seed | val_acc | val_macro_f1 | val_mae | Durasi (s) | Confusion Matrix Validasi (baris=asli 0..3, kolom=prediksi 0..3) |
|---:|---:|---:|---:|---:|---|
| 1 | 0.946759 | 0.951703 | 0.053241 | 78.3 | `[[36, 0, 0, 0], [1, 131, 12, 0], [0, 0, 180, 0], [0, 0, 10, 62]]` |
| 2 | 0.942130 | 0.944408 | 0.057870 | 83.8 | `[[36, 0, 0, 0], [0, 137, 7, 0], [0, 0, 174, 6], [0, 0, 12, 60]]` |
| 3 | 0.956019 | 0.961027 | 0.043981 | 82.8 | `[[36, 0, 0, 0], [1, 132, 11, 0], [0, 0, 180, 0], [0, 0, 7, 65]]` |
| **Rerata ± SB** | **0.9483 ± 0.0058** | **0.9524 ± 0.0068** | **0.0517 ± 0.0058** | **81.6 ± 2.4** | — |

Seluruh metrik per run terekam otomatis di `results/122450138/tl_metrics.csv` dan `results/122450138/metrics.json`.

## Ekspor dan verifikasi ONNX

Untuk mengekspor model ke format ONNX (baik *end-to-end* dari log-mel `(B, 64, 101)` ke `logits (B, 4)`
maupun khusus *classifier head* `(B, 512)` ke `logits (B, 4)`) dan memverifikasi kesamaan prediksinya
dengan `onnxruntime`:

```powershell
python models/122450138/export_onnx.py
```

Hasil verifikasi pada 432 jendela validasi menunjukkan kecocokan prediksi kelas **100,00%** antara
PyTorch dan ONNX Runtime (`val_acc = 0.9560` pada checkpoint seed 3, selisih logit maksimum `1.91e-05`,
ukuran ONNX *end-to-end* `17.68 MiB`, ukuran ONNX *head-only* `259.10 KiB`).
