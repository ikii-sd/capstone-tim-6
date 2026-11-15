# Catatan Sesi dan Pemeriksaan Mutu Data — Tim 6

## Identitas sesi
- **Tim:** 6 — Taksiran jumlah alat bersuara yang menyala
- **Sesi digunakan:** `sesi-20261113-200606`
- **Tanggal sesi:** 13 November 2026
- **Sumber:** `tim06_sesi-20261113-200606.tar.gz`
- **Status sesi:** log berakhir dengan `Selesai` pada 2026-11-13 21:51:44.174.
- **Hash SHA-256 `label.csv`:** `fe963aafa87c7705fa3b6567049ff322eb1fd9121e58fe690fd367c5f5e90a4a`
- **`data_hash` repository:** `49995c7fa09a800959bab64782bb80fa`
- **Metode perhitungan:** Fungsi `data_hash()` pada `src/common/manifest.py`, menggunakan nama dan isi tujuh CSV yang terdaftar di `data/MANIFEST.json`, tanpa parameter tambahan.
- **Status sinkronisasi:** Hash berhasil dihitung secara lokal; kesamaan hash seluruh anggota tim belum dikonfirmasi.

## Rancangan dan kelengkapan label
- **288/288 kondisi** tercatat; **24 kombinasi** faktor dengan **12 ulangan** tiap kombinasi.
- Faktor: kipas {0,128,255}, pompa {0,200}, buzzer {0,1}, lampu {0,255}.
- Target kelas diturunkan dari `(kipas > 0) + (pompa > 0) + (buzzer == 1)`; lampu tidak dihitung.
- Durasi kondisi sekitar 20 detik dengan jeda sekitar 2 detik.
- Kolom `pintu_awal` dan `pintu_akhir` pada `label.csv` kosong; tidak digunakan untuk target kelas Tim 6.

## Ringkasan QC

| Komponen | Temuan | Status |
|---|---|---|
| `label.csv` | 288 kondisi, 24 kombinasi × 12 ulangan | Lulus struktur |
| `log.txt` | Baris akhir memuat `Selesai` | Lulus |
| `aktuator.csv` | 2.313 baris; perintah kipas, pompa, buzzer, lampu tersedia. Perintah pompa tercatat, tetapi tidak membuktikan arus fisik pompa. Nilai lampu ON tercatat `1` pada aktuator dan `255` pada label (kemungkinan representasi berbeda). | Perlu catatan |
| `daya.csv` | 1.198.233 baris; kanal yang ditemukan hanya `kipas`. Arus kipas meningkat saat PWM meningkat. Kanal arus pompa tidak ditemukan sehingga kenaikan arus ketika pompa=200 **belum bisa diuji**. | Perlu klarifikasi pengelola |
| `imu.csv` | 2.395.811 baris total; 2.167.847 sampel masuk ke rentang 288 kondisi. Median 7.999 sampel/kondisi dari target sekitar 8.000. Semua kondisi punya sampel. | Lulus sebagian; kekurangan sampel |
| `imu.csv` — kelengkapan | 109 kondisi memiliki kurang dari 7.600 sampel; 57 kondisi kurang dari 7.000. Kondisi terendah: #252 (4.796), #5 (4.798), #102 (5.196), #87 (5.198), #9 (5.596). | Perlu evaluasi |
| `imu.csv` — respons kipas | Variasi giroskop pada PWM 255 cenderung lebih tinggi daripada PWM 0; pada PWM 128 respons relatif kecil. | Indikasi respons, bukan validasi fisik penuh |
| `audio_index.csv` dan WAV | 106 rekaman terindeks, sample rate indeks 16.000 Hz. Sampel WAV awal/tengah/akhir yang diperiksa dapat dibaca dan memiliki sinyal. Rekaman berupa segmen berkelanjutan; jumlah file tidak harus sama dengan jumlah kondisi. | Pemeriksaan awal lulus; pemeriksaan menyeluruh belum selesai |
| `lingkungan.csv` | 6.175 baris; suhu dan lux tersedia; `rh_persen` kosong. | Perlu catatan |
| `digital.csv` | Hanya header, tanpa baris data. | Perlu catatan; belum tentu relevan |

## Kondisi yang dikeluarkan
**Belum ada kondisi yang diputuskan untuk dikeluarkan (0 kondisi).** Seluruh 288 kondisi dipertahankan sementara untuk evaluasi berikutnya. Ini **bukan** pernyataan bahwa seluruh kondisi sudah lolos semua pemeriksaan mutu.

Kondisi #252, #5, #102, #87, dan #9 diprioritaskan untuk ditinjau karena memiliki jumlah sampel IMU terendah berdasarkan pemeriksaan awal. Secara keseluruhan, ditemukan 109 kondisi dengan kurang dari 7.600 sampel dan 57 kondisi dengan kurang dari 7.000 sampel. Daftar terperinci kondisi tersebut belum disertakan dalam repository dan perlu disiapkan apabila diperlukan untuk pemeriksaan lanjutan.

## Tindak lanjut sebelum QC final
1. **Konfirmasi kanal pompa:** tanyakan apakah arus pompa direkam di berkas lain atau memang tidak tersedia. Jangan menyimpulkan pompa kering/tersumbat hanya dari absennya kanal.
2. **Audio:** cek integritas seluruh WAV, kesinambungan waktu, serta perbedaan sinyal saat buzzer=0 dan buzzer=1; lakukan dengar sampel representatif bila memungkinkan.
3. **IMU:** tinjau kondisi dengan sampel kurang dan tentukan apakah ada yang perlu dikecualikan sesuai kriteria tim.
4. **Dokumentasi:** pastikan seluruh anggota memakai berkas `label.csv` yang sama dan nilai `data_hash` yang identik dalam `data/MANIFEST.json`.
5. **Konfirmasi representasi lampu:** nilai ON `255` di label dan `1` di aktuator perlu dipahami sebagai representasi PWM/boolean sebelum dinyatakan masalah.

## Status akhir
**QC sementara — belum final.** Kelengkapan rancangan 288 kondisi terpenuhi, tetapi validasi arus pompa dan pemeriksaan audio menyeluruh masih terbuka. Keputusan pengecualian kondisi perlu diperbarui setelah tindak lanjut.
