# Catatan sesi — Tim 6

Pemeriksaan mutu menurut bagian 8 dokumen *Metode Eksperimen Lapangan* dan bagian 5
keterangan kasus `tim-06`. Diperiksa 14 Nov 2026 oleh Boby (122450048).

## Sesi yang dipakai

`sesi-20261113-200606` — 13 Nov 2026, 20.06–21.51 WIB, slot otomatis tanpa operator.
Satu-satunya sesi yang dipakai untuk latih, validasi, dan uji.

Dua arsip lain pada kartu Data meja (13 Nov 17.43–17.45, 729 KB; 13 Nov 18.08–19.53, 43,5 MB)
belum diunduh dan belum diperiksa. Keduanya tidak dipakai. Bila salah satunya sesi siang dengan
bising latar, dokumen metode mengizinkannya sebagai **uji tambahan**, bukan data latih.

## Hasil pemeriksaan

| Pemeriksaan | Cara | Hasil |
|---|---|---|
| Jumlah kondisi | baris `label.csv` | **288** (24 kombinasi × 12 ulangan, tiap ulangan 24 kondisi) — sesuai rencana |
| Log selesai | baris terakhir `log.txt` | `Selesai.` setelah `kondisi 288/288 selesai` |
| Sesi asli, bukan simulasi | `manifest.json` | `simulasi: false`, perekam versi 1.6, host `sditera-civ` |
| Durasi kondisi | `t_selesai_host − t_mulai_host` | 20,000–20,001 detik untuk seluruh 288 kondisi |
| Keutuhan sidik | sha256 `label.csv` | `fe963aaf…5e90a4a`, cocok dengan `manifest.json` sesi |
| Audio | `audio_index.csv` + 106 WAV | laju 16000 Hz seluruhnya; `jumlah_sampel` cocok dengan isi tiap WAV; audio menutupi seluruh sesi (mulai 0,02 detik sebelum kondisi pertama, selesai 2,5 detik sesudah kondisi terakhir); tidak ada kondisi di luar rentang audio |
| Kesesuaian label | energi log-mel per faktor, dipasangkan | lihat di bawah |
| Kondisi terganggu | `digital.csv`, kolom `pintu_awal`/`pintu_akhir` | kosong; slot otomatis tanpa orang, tidak ada lembar sesi, tidak ada kondisi yang dikeluarkan |

### Celah antar-potongan WAV

Audio direkam sebagai 106 potongan berurutan (±60 detik), bukan satu berkas per kondisi.
Batas antar-potongan tidak bersambung sempurna: selisih −14 sampai +21 sampel (maksimum 1,3 ms),
pada 82 dari 105 batas; 75 dari 288 kondisi melintasi satu batas.

Pemuat mengiris tiap kondisi dari garis waktu `t_mulai_host` tiap potongan, bukan dengan
menyambung potongan begitu saja, sehingga penyimpangan tidak menumpuk sepanjang sesi
(total pergeseran bila disambung mentah: 46 ms). Celah ≤ 5 ms diisi interpolasi linear dan
dihitung; celah lebih panjang membuat pemuatan gagal. Sesi ini: **763 sampel (47,7 ms dari
5760 detik rekaman, 0,0008 %)** ditambal. Pengaruhnya pada log-mel dapat diabaikan.

### Kesesuaian label (pemeriksaan akustik)

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

**Pompa.** Sensor arus pompa belum terpasang di meja, sehingga `daya.csv` tidak bisa dipakai
untuk memastikan pompa menyala; pemeriksaan hanya lewat suara. Pompa terdengar
(rata-rata +0,69, median +0,45, naik pada 69 % pasangan), tetapi merupakan alat **paling lemah**
di antara ketiganya. Ini risiko yang perlu diawasi: kekeliruan model kemungkinan besar
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
3. Dua arsip lain pada kartu Data meja belum diperiksa (lihat atas).

## Berkas yang tidak di-commit

Sesuai `.gitignore` (`data/*` kecuali `data/MANIFEST.json`), isi folder sesi tidak masuk ke
GitHub: `audio/` (106 WAV, 176 MB), `imu.csv` (129 MB), `daya.csv` (51 MB), dan CSV sensor lain.
Dua berkas terbesar melampaui batas 100 MB per berkas di GitHub, jadi memang tidak dapat
di-commit apa adanya.

Dokumen metode (bagian 7.5) meminta `label.csv`, CSV sensor, dan `manifest.json` dimasukkan ke
`data/`. Hal ini bertentangan dengan `.gitignore` bawaan starter. **Perlu keputusan tim dan
pembimbing**: melonggarkan `.gitignore` untuk `label.csv`, `audio_index.csv`, dan `manifest.json`
saja (ketiganya kecil, total 31 KB), atau tetap menyimpan seluruh folder sesi di luar repo.
Selama belum diputuskan, ketiga berkas itu tetap di luar repo dan hanya sidiknya yang terekam
lewat `data/MANIFEST.json`.

Arsip lengkap dan tautan penyimpanan tim dicatat di Papan Tim Workbench.
