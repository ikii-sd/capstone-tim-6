# Catatan model 122450138 — Transfer Learning PANNs Cnn6

## Arsitektur

Model memakai bobot AudioSet resmi PANNs Cnn6 dari
https://zenodo.org/records/3987831. Frontend waveform dilewati agar model menerima
log-mel tim melalui `src.protokol.data.muat()`. Masukan berukuran `(N, 64, 101)`
berasal dari audio 16 kHz dua detik. Skala dan bias awal PANNs dipakai dengan
statistik normalisasi latih tim.

Konfigurasi utama membekukan `bn0` dan `conv_block1..3`. Fitur awal dihitung
satu kali per split. `conv_block4`, `fc1`, serta classifier 512 → 128 → 4 dilatih
bersama. Checkpoint dipilih dari akurasi validasi tertinggi selama 25 epoch.

## Optimizer, regularisasi, dan tuning

AdamW memakai learning rate 0,001, weight decay 0,01, batch 64, dan dropout 0,3.
Pembekuan lapisan awal membatasi parameter yang diperbarui. Weight decay dan
dropout mengendalikan pembaruan bobot dan mengurangi overfitting. Konfigurasi ini
melanjutkan pencarian hiperparameter yang dicatat pada commit `05fab61`.

Normalisasi embedding berbasis statistik latih diterapkan pada mode backbone
beku penuh (`--freeze-blocks 4`). Mode partial fine-tuning memakai normalisasi
identitas. Label Norm Emb pada catatan terdahulu telah diperbaiki sesuai kode.
`--tanpa-norm-emb` memerlukan `--freeze-blocks 4`.

## Pengujian ulang tiga seed dan dua ablasi, 25 November 2026

Sesi primer `sesi-20261113-200606` memakai split tetap per ulangan dengan seed
2026. Terdapat 3.024 jendela latih, 432 validasi, dan 1.728 uji. Seluruh angka
berikut berasal dari validasi. Simpangan baku memakai pembagi n−1. Variasi seed
menggambarkan variasi pelatihan pada satu ulangan validasi tetap.

Pelatihan ulang memakai NVIDIA GeForce GTX 1650 pada laptop. Metadata baru
mencatat perangkat aktual. Durasi mencakup pemuatan data dan pelatihan sampai
checkpoint tersimpan. Opsi `--device cpu` tersedia untuk pengukuran anggaran
pelatihan CPU sesuai protokol atau kebutuhan pembimbing.

| Konfigurasi | Seed | Akurasi | Macro-F1 | MAE | Durasi (s) |
|---|---:|---:|---:|---:|---:|
| Partial fine-tuning | 1 | 0.942130 | 0.940936 | 0.057870 | 72.2 |
| Partial fine-tuning | 2 | 0.939815 | 0.941399 | 0.060185 | 71.7 |
| Partial fine-tuning | 3 | 0.962963 | 0.962599 | 0.037037 | 72.5 |
| Partial fine-tuning | 1–3 | 0.948303 ± 0.012749 | 0.948311 ± 0.012376 | 0.051698 ± 0.012749 | 72.133333 ± 0.404145 |
| Ablasi 1, backbone beku penuh | 1 | 0.844907 | 0.862451 | 0.164352 | 40.3 |
| Ablasi 1, backbone beku penuh | 2 | 0.851852 | 0.866243 | 0.152778 | 41.3 |
| Ablasi 1, backbone beku penuh | 3 | 0.854167 | 0.866560 | 0.150463 | 36.8 |
| Ablasi 1, backbone beku penuh | 1–3 | 0.850309 ± 0.004819 | 0.865085 ± 0.002286 | 0.155864 ± 0.007441 | 39.466667 ± 2.362908 |
| Ablasi 2, dropout dan weight decay 0 | 1 | 0.949074 | 0.946441 | 0.050926 | 70.6 |
| Ablasi 2, dropout dan weight decay 0 | 2 | 0.928241 | 0.929841 | 0.076389 | 85.9 |
| Ablasi 2, dropout dan weight decay 0 | 3 | 0.946759 | 0.947190 | 0.053241 | 75.7 |
| Ablasi 2, dropout dan weight decay 0 | 1–3 | 0.941358 ± 0.011418 | 0.941157 ± 0.009807 | 0.060185 ± 0.014080 | 77.400000 ± 7.790379 |

Ablasi pertama membekukan seluruh backbone pada 25 epoch. Ablasi kedua
menghilangkan dropout dan weight decay secara bersama. Kontribusi individual
kedua regularisasi memerlukan eksperimen terpisah. Pada pengujian ulang ini,
pembekuan penuh memiliki akurasi rerata lebih rendah dibanding partial FT.

## Analisis kesalahan dan ONNX

Pada gabungan prediksi tiga seed utama, kesalahan terbanyak adalah kelas 3 ke 2 sebanyak 37; kelas 1 ke 2 sebanyak 11; kelas 2 ke 3 sebanyak 10.
Hitungan tersebut menjumlahkan tiga prediksi pada set validasi yang sama.
Matriks konfusi tiap seed tersimpan dalam metadata eksperimen.

ONNX seed 1 berukuran 18103.92 KiB
(17.68 MiB). Prediksi kelas ONNX dan PyTorch cocok
100.00% pada 432 jendela validasi, dengan
akurasi 0.942130, MAE 0.057870, dan selisih logit maksimum
3.34e-06. Latensi CPU batch 1 memiliki rerata 21.700 ms
dan p95 25.502 ms. Pengukuran memakai satu thread ONNX Runtime,
10 warm-up dan 100 pengulangan. Cakupan pengukuran adalah log-mel ternormalisasi
ke logits. Perekaman dan praproses audio memerlukan pengukuran terpisah.


## Reproduksi

```powershell
python models/122450138/run.py --seed 1
python models/122450138/run.py --seed 2
python models/122450138/run.py --seed 3
python models/122450138/run.py --seed 1 --freeze-blocks 4
python models/122450138/run.py --seed 1 --dropout 0 --wd 0
python -m pip install onnx onnxruntime
python models/122450138/export_onnx.py --out data/tl_panns_cnn6.onnx
```

Ulangi dua perintah ablasi untuk seed 2 dan 3. `tl_metrics.csv` mempertahankan
kombinasi konfigurasi, seed, dan hash data. `results/122450138/experiments/`
menyimpan `pred_val.npy`, `metrics.json`, dan `run.json` per eksperimen.
Metadata memuat konfigurasi, perangkat, hash kode, MAE, serta matriks konfusi.
Hasil utama di direktori NIM mengikuti kontrak evaluator dosen dan saat ini
memakai seed 1.

`tl_best.pt` adalah checkpoint lokal terakhir dan diabaikan Git. Ekspor
memerlukan checkpoint pelatihan. `onnx_verification.json` mencatat seed, hash
checkpoint dan ONNX, ukuran, kesesuaian prediksi, serta latensi CPU.
Berkas ONNX end-to-end di `data/` diabaikan Git dan dapat dibuat ulang.

## Batas evaluasi

Hash evaluator saat pengujian adalah `ffcb1966eec8bf6b285607a0e19e97c0`. Manifest saat ini
mencantumkan tujuh CSV. Penjaga Data perlu meninjau identitas WAV agar hash
mencakup audio yang dipakai model. Perubahan manifest memerlukan penghitungan
ulang artefak semua anggota. Metrik resmi klasifikasi starter berupa akurasi
dan macro-F1. MAE kasus tim dicatat terpisah dalam metadata eksperimen.
