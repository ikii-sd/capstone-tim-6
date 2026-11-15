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


## Pemeriksaan lanjutan oleh Boby (14 November 2026)

Menurut catatan Boby (122450048), sesi berlangsung 13 November 2026 pukul 20.06–21.51 WIB, dengan slot otomatis tanpa operator. Ia melaporkan `manifest.json` sesi menunjukkan `simulasi: false`, perekam versi 1.6, host `sditera-civ`; durasi setiap kondisi 20,000–20,001 detik; dan checksum `label.csv` cocok dengan manifest sesi. Pemeriksaan Boby meliputi seluruh indeks WAV, kecocokan jumlah sampel dengan isi WAV, cakupan waktu audio, serta pemeriksaan energi akustik per faktor. Ini tidak berarti seluruh QC fisik/lingkungan dan keputusan eksklusi kondisi sudah final.

### Pemeriksaan lanjutan Boby: celah antar-potongan WAV

Audio direkam sebagai 106 potongan berurutan (±60 detik), bukan satu berkas per kondisi.
Batas antar-potongan tidak bersambung sempurna: selisih −14 sampai +21 sampel (maksimum 1,3 ms),
pada 82 dari 105 batas; 75 dari 288 kondisi melintasi satu batas.

Pemuat mengiris tiap kondisi dari garis waktu `t_mulai_host` tiap potongan, bukan dengan
menyambung potongan begitu saja, sehingga penyimpangan tidak menumpuk sepanjang sesi
(total pergeseran bila disambung mentah: 46 ms). Celah ≤ 5 ms diisi interpolasi linear dan
dihitung; celah lebih panjang membuat pemuatan gagal. Sesi ini: **763 sampel (47,7 ms dari
5760 detik rekaman, 0,0008 %)** ditambal. Dampak celah yang ditambal terhadap hasil model masih perlu dinilai bila relevan.

### Pemeriksaan lanjutan Boby: kesesuaian label (akustik)

Energi log-mel rata-rata dibandingkan **berpasangan**: dua kondisi yang hanya berbeda pada satu
faktor, di dalam ulangan yang sama. Perbandingan langsung antar-kelompok menyesatkan karena
kipas ikut mengisi pita yang sama dengan pompa.

| Faktor | Pita | Selisih rata-rata | Naik pada |
|---|---|---|---|
| Kipas 255 vs 0 | 50–500 Hz | +2,11 | 83 dari 96 pasangan |
| Buzzer 1 vs 0 | 1500–3000 Hz | +1,64 | 139 dari 144 pasangan |
| Pompa 200 vs 0 | 500–1500 Hz | +0,69 | 99 dari 144 pasangan |
| Lampu 255 vs 0 (pengecoh) | 0–8000 Hz | +0,12 | — |

Energi total naik berurutan menurut kelas: −5,06 (0 alat), −3,55 (1), −2,79 (2), −2,25 (3).
Kipas 128 (−2,14) memang lebih pelan daripada kipas 255 (−0,57) tetapi lebih keras daripada
kipas 0 (−2,68), jadi taraf 128 benar dihitung sebagai menyala.

**Pompa.** Kanal arus pompa tidak ditemukan di `daya.csv`, sehingga tidak bisa dipakai
untuk memastikan pompa menyala; pemeriksaan tambahan dilakukan lewat indikator akustik.
Status pemasangan sensor arus pompa perlu dikonfirmasi kepada pengelola. Respons akustik pompa tercatat
(rata-rata +0,69, median +0,45, naik pada 69 % pasangan), tetapi merupakan indikasi **paling lemah**
di antara ketiganya. Ini risiko yang perlu diawasi: kekeliruan model berpotensi
terkonsentrasi pada pasangan kondisi yang hanya berbeda pompa. Lampu hampir tidak berpengaruh
(+0,12), yang memang diharapkan dari pengecoh.


## Kejanggalan yang tercatat

1. Mikrofon menolak 16000 Hz (`PaErrorCode -9997`), sehingga perekam merekam pada 48000 Hz lalu
   menurunkannya ke 16000 Hz (`log.txt` baris 4). Seluruh audio tetap 16 kHz seperti dituntut
   protokol, tetapi penurunan laju ini berlaku untuk **semua** rekaman sesi ini dan perlu
   disebut di laporan. Bila sesi lain direkam langsung pada 16 kHz, keduanya tidak sepenuhnya
   setara.
2. `digital.csv` hanya berisi baris tajuk (28 bita). Tidak ada kejadian pintu atau PIR tercatat.
   Wajar untuk ruang kosong dan tertutup, tetapi berarti tidak ada bukti sensor bahwa ruangan
   benar-benar kosong selama sesi.
3. Dua arsip lain yang disebut dalam catatan Boby belum diperiksa pada saat pemeriksaan 14 November 2026; status perlu diperbarui bila kemudian sudah diperiksa.

## Berkas yang tidak di-commit

Menurut konfigurasi `.gitignore` yang dijelaskan Boby saat pemeriksaan, isi folder sesi tidak masuk ke
GitHub: `audio/` (106 WAV, 176 MB), `imu.csv` (129 MB), `daya.csv` (51 MB), dan CSV sensor lain.
Dua berkas terbesar melampaui batas 100 MB per berkas di GitHub, jadi memang tidak dapat
di-commit apa adanya.

Dokumen metode (bagian 7.5) meminta `label.csv`, CSV sensor, dan `manifest.json` dimasukkan ke
`data/`. Hal ini bertentangan dengan `.gitignore` bawaan starter. **Perlu keputusan tim dan
pembimbing**: melonggarkan `.gitignore` untuk `label.csv`, `audio_index.csv`, dan `manifest.json`
saja (ketiganya kecil, total 31 KB), atau tetap menyimpan seluruh folder sesi di luar repo.
Status keputusan dan file yang sudah masuk repo harus disesuaikan dengan hasil merge `.gitignore` dan keadaan repository terbaru.

Arsip lengkap dan tautan penyimpanan tim dicatat di Papan Tim Workbench.
## Tindak lanjut sebelum QC final
1. **Konfirmasi kanal pompa:** tanyakan apakah arus pompa direkam di berkas lain atau memang tidak tersedia. Jangan menyimpulkan pompa kering/tersumbat hanya dari absennya kanal.
2. **Audio:** verifikasi hasil pemeriksaan teknis Boby, lakukan dengar sampel representatif bila memungkinkan, dan catat keputusan QC menyeluruh.
3. **IMU:** tinjau kondisi dengan sampel kurang dan tentukan apakah ada yang perlu dikecualikan sesuai kriteria tim.
4. **Dokumentasi:** pastikan seluruh anggota memakai berkas `label.csv` yang sama dan nilai `data_hash` yang identik dalam `data/MANIFEST.json`.
5. **Konfirmasi representasi lampu:** nilai ON `255` di label dan `1` di aktuator perlu dipahami sebagai representasi PWM/boolean sebelum dinyatakan masalah.

## Status akhir
**QC sementara — belum final.** Kelengkapan rancangan 288 kondisi terpenuhi, tetapi validasi arus pompa dan validasi QC audio secara menyeluruh masih terbuka meskipun pemeriksaan teknis Boby telah dilaporkan. Keputusan pengecualian kondisi perlu diperbarui setelah tindak lanjut.
