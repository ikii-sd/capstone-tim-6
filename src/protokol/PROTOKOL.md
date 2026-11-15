# Protokol evaluasi tim — Tim 6

Diisi Penjaga Data & Evaluasi pada Sprint 0, digabung ke `main` lewat *pull request* yang
disetujui pembimbing, lalu **dibekukan**. Perubahan setelah itu hanya lewat *pull request*
baru yang disetujui pembimbing.

| Butir | Isi |
|---|---|
| Kasus (dari kartu Kasus tim) | Taksiran jumlah alat bersuara yang menyala (t06) |
| Sumber dataset | Data primer meja, sesi otomatis `sesi-20261113-200606` (13 Nov 2026, 20.06–21.51 WIB, `simulasi=false`, log berakhir `Selesai`). Rencana: `rencana/t06-hitung-alat-suara.yaml` (seed 1006, 12 ulangan, kondisi 20 detik, jeda 2 detik). 288 kondisi = 24 kombinasi × 12 ulangan. Berkas yang menentukan `data_hash` tercantum di `data/MANIFEST.json`; pemeriksaan mutu di `data/CATATAN-SESI.md`. |
| Jenis tugas (`TUGAS`) | klasifikasi (jumlah alat bersuara 0–3) |
| Target / label | jumlah aktuator bersuara (kipas, pompa, buzzer) dari relay, otomatis; lampu pengecoh tidak dihitung |
| Ukuran data latih / validasi / uji | Per ulangan: 7 / 1 / 4 dari 12 ulangan. 18 jendela per kondisi. Jumlah jendela: **3024 / 432 / 1728** (total 5184). Sebaran kelas 0/1/2/3 per ulangan: 2 / 8 / 10 / 4 kondisi, jadi seimbang antar-bagian. |
| Cara split | Satuan pemisahan = **ulangan**: semua jendela dari satu ulangan berada di satu bagian (jendela saling tumpang tindih 1 detik). 12 ulangan dibagi 3 lipatan @ 4 ulangan (acak tetap, seed 2026); uji = 1 lipatan (`lipatan=0` → uji ulangan 7, 2, 10, 9; validasi ulangan 1). Sisa 8 ulangan dibagi dengan `split.indeks` seed 2026, porsi validasi bawaan 10 % → 7 latih, 1 validasi. `muat()` gagal otomatis bila ada ulangan di lebih dari satu bagian. |
| Metrik utama untuk komparasi | Akurasi dan MAE (selisih jumlah alat prediksi dan sebenarnya), sesuai kartu Kasus dan `rencana/*.yaml`. **Perlu keputusan pembimbing:** `src/common/evaluate.py` (milik starter, tidak boleh diubah) menghitung `acc` dan `macro_f1` untuk tugas klasifikasi, bukan MAE, dan tabel `run_all.py` hanya memuat `val_acc` dan `val_macro_f1`. Pilihan: (a) MAE dihitung terpisah dan dilaporkan di `reports/`, atau (b) metrik komparasi diubah menjadi Akurasi + macro-F1. |
| Praproses yang sama untuk semua model | Audio mono 16 kHz dari `audio/`. Audio meja direkam sebagai 106 potongan WAV berurutan (±60 detik), bukan satu berkas per kondisi, sehingga tiap kondisi diiris dari garis waktu `t_mulai_host` memakai `audio_index.csv`. Buang 1 detik pertama tiap kondisi (20 detik); jendela 2 detik bergeser 1 detik (18 jendela per kondisi); log-mel 64 pita (FFT 1024, geseran 320 sampel, 0–8000 Hz) → bentuk (64, 101); normalisasi per pita mel dari data latih saja. Batas antar-potongan WAV meleset beberapa sampel (buffer perekam); celah ≤ 5 ms diisi interpolasi linear dan dihitung, celah lebih panjang membuat pemuatan gagal. Pada sesi ini total 763 sampel (47,7 ms dari 5760 detik) ditambal. |
| Anggaran komputasi per run | ≤ 20 menit CPU laptop (atau yang disetujui pembimbing). `muat()` pada data asli ≈ 7 detik; dipanggil dua kali per run (di `run.py` dan `evaluate.py`), jadi cache belum diperlukan. |
| Evaluasi data uji | sekali, oleh Penjaga Data, pada sprint terakhir (`--final`) |
| `data_hash` saat dibekukan | `c52baed61837192bf56ffc47d2b70a88` (dari `data/MANIFEST.json`; cocokkan dengan `results/baseline/metrics.json` setelah baseline dijalankan) |

Empat parameter log-mel (FFT 1024, geseran 320 sampel, 0–8000 Hz, 64 pita) adalah usulan tim dan
masih perlu dikonfirmasi pembimbing. Jumlah pita dan panjang jendela mengikuti kartu Kasus
(log-mel 64 pita, 2 detik); FFT dan geseran dipilih agar satu jendela 2 detik menjadi tepat
101 bingkai.

Disetujui pembimbing pada: … (tautan *pull request*)
