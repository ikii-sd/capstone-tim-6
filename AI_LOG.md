# AI_LOG — Tim 6

Satu baris per pemakaian AI yang bermakna (ChatGPT, Claude, Copilot, Bravais, dan sejenisnya).
Ringkas dan jujur; transkrip penuh tidak diminta. Yang dinilai bukan "pakai AI atau tidak",
melainkan "mengerti atau tidak" — isi kolom terakhir dengan apa yang Anda ubah dari keluarannya.

| Tanggal | Siapa (NIM) | Alat | Untuk apa | Apa yang diubah dari keluarannya |
|---|---|---|---|---|
| 2026-11-15 | 122450048 | Claude (Opus 5) | Mengisi `_baca_sesi()` di `src/protokol/data.py`: membaca `label.csv` dan `audio_index.csv`, mengiris tiap kondisi dari potongan WAV kontinu | PERIKSA DAN ISI SENDIRI |
| 2026-11-15 | 122450048 | Claude (Opus 5) | Pemeriksaan mutu sesi `20261113-200606` (`data/CATATAN-SESI.md`), pengisian `PROTOKOL.md` dan `data/MANIFEST.json`, penambahan uji pemotong audio di `uji_data.py` | PERIKSA DAN ISI SENDIRI |

<!--
Catatan untuk Boby, hapus blok ini setelah kolom terakhir diisi.

Kolom terakhir harus kalimat Anda sendiri dan harus jujur. Bahan yang benar-benar terjadi
pada sesi 14-15 Nov, pilih yang sesuai dan tulis ulang dengan kata-kata Anda:

- Menjalankan dan memverifikasi seluruh keluaran di laptop sendiri sebelum di-commit
  (uji protokol, baseline, CNN tiga seed), bukan menerima begitu saja.
- Menolak saran menjalankan ulang tiga seed lewat run_all.py setelah memeriksa bahwa
  dokumen metode hanya mewajibkan tiga seed untuk konfigurasi akhir, bukan tiap run.
  Saran AI semula keliru di titik ini.
- Menangkap bahwa kartu #6 terlewat karena pengerjaan langsung melompat ke CNN,
  lalu meminta urutannya dibetulkan.
- Mempertanyakan peringatan "memakai rekaman PALSU" yang muncul saat uji, sampai jelas
  bahwa itu berasal dari uji bagian 7 yang memang menyetel DATA_SINTETIS sendiri.
- Membatalkan penulisan ulang riwayat commit (rebase) setelah menimbang risikonya pada
  cabang yang sedang ditinjau di PR.

Jika ada pemakaian AI sebelum 14 Nov yang belum tercatat, tambahkan barisnya sendiri.
-->
