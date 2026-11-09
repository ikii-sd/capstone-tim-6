# Catatan model 122450138 — Backlog #13

Model menerima log-mel ternormalisasi dari `src.protokol.data.muat()` dengan bentuk
`(N, 64, 101)` untuk jendela audio dua detik. Ekstraktor PANNs Cnn6 dimuat dari
[bobot AudioSet resmi](https://zenodo.org/records/3987831), dibekukan dalam mode
evaluasi, dan menghasilkan embedding 512 dimensi. Classifier memetakan embedding
ke empat kelas (0–3). Cnn6 dipilih karena checkpoint sekitar 24 MB dan
embedding dapat dihitung satu kali per split.

Front-end waveform Cnn6 dilewati agar model memakai fitur bersama dari tim.
PANNs memakai setelan log-mel yang berbeda saat prapelatihan. Di sini statistik
normalisasi latih tim menggantikan statistik awal PANNs, sedangkan skala dan
bias terlatih dipertahankan. Dampak perbedaan setelan fitur perlu diukur pada
data simulasi resmi.

## Alasan optimizer

AdamW menyesuaikan langkah per parameter classifier. Konfigurasi awal memakai
learning rate 0,001, weight decay 0,01, 10 epoch, dan batch classifier 128.
Kelas dilatih dengan cross-entropy.

## Regularisasi

Backbone dibekukan. Classifier memakai dropout 0,3 dan weight decay.

## Menjalankan pengujian awal

```powershell
python models/122450138/run.py --seed 1
```

Jalankan setelah `data.muat()` dapat membaca simulasi resmi. PyTorch mengunduh
checkpoint pada pemakaian pertama. Untuk penggunaan luring, simpan
`Cnn6_mAP=0.343.pth` dari Zenodo di subfolder `checkpoints` pada direktori yang
ditampilkan oleh `python -c "import torch; print(torch.hub.get_dir())"`.

Evaluator starter menulis `results/122450138/metrics.json` dari prediksi validasi.
Opsi `--final` disediakan untuk evaluasi uji pada sprint terakhir.

## Verifikasi 9 November 2026

Bobot resmi berhasil dimuat. Uji awal menghasilkan embedding `(2, 512)` dan
skor `(2, 4)` untuk log-mel `(2, 64, 101)`. Pada salinan sementara dengan audio
sintetis, perintah `--seed 1` berhasil sampai evaluator dan menghasilkan
`pred_val.npy` serta `metrics.json` validasi. Pengujian di repo dengan data resmi
masih terhenti karena `_baca_sesi()` belum diimplementasikan dan data belum
tersedia secara lokal.

## Pencarian hyperparameter, ablation, dan hasil tiga seed

Menunggu uji pada data simulasi resmi. Konfigurasi di atas merupakan titik awal.
