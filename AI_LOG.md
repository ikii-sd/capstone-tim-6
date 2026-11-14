# AI_LOG — Tim 6

Satu baris per pemakaian AI yang bermakna (ChatGPT, Claude, Copilot, Bravais, dan sejenisnya).
Ringkas dan jujur; transkrip penuh tidak diminta. Yang dinilai bukan "pakai AI atau tidak",
melainkan "mengerti atau tidak" — isi kolom terakhir dengan apa yang Anda ubah dari keluarannya.

| Tanggal | Siapa (NIM) | Alat | Untuk apa | Apa yang diubah dari keluarannya |
|---|---|---|---|---|
| 2026-11-15 | 122450048 | Claude (Opus 5) | Mengisi `_baca_sesi()` di `src/protokol/data.py`: membaca `label.csv` dan `audio_index.csv`, lalu mengiris tiap kondisi dari potongan WAV yang kontinu | Tidak diterima begitu saja. Saya jalankan sendiri `uji_data`, baseline, dan `run.py` di laptop sampai angkanya cocok dengan PROTOKOL.md (3024/432/1728), dan saya telusuri peringatan "rekaman PALSU" sampai jelas itu berasal dari uji bagian 7 yang memang menyetel `DATA_SINTETIS` sendiri, bukan dari data yang dipakai |
| 2026-11-15 | 122450048 | Claude (Opus 5) | Pemeriksaan mutu sesi `20261113-200606` (`data/CATATAN-SESI.md`), pengisian `PROTOKOL.md` dan `data/MANIFEST.json`, serta penambahan uji pemotong audio di `uji_data.py` | Saya cocokkan sarannya dengan dokumen tugas dan dua kali mengoreksi arah kerjanya: saran menjalankan ulang tiga seed saya batalkan setelah memastikan dokumen metode hanya mewajibkan tiga seed untuk konfigurasi akhir, dan saya menangkap bahwa kartu #6 terlewat karena pengerjaan langsung melompat ke CNN |