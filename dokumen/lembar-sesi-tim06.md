# LEMBAR SESI EKSPERIMEN — TIM 6

**Judul:** Taksiran Jumlah Alat Bersuara yang Menyala

**Pembimbing:** Ardika Satria

**Tanggal rencana awal:** Kamis, 5 November 2026

**Tanggal sesi aktual:** Jumat, 13 November 2026

**Jenis sesi:** Eksperimen otomatis

**ID sesi:** `sesi-20261113-200606`

**Tanggal verifikasi lanjutan:** 28 November 2026

Dokumen ini dilengkapi secara retrospektif berdasarkan dataset, log sesi, manifest, dan hasil pemeriksaan mutu (QC).

## A. Pembagian Peran

| Nama | Peran |
|---|---|
| David Boby C. Nainggolan | Operator Perekam |
| Ahmad Rizqi | Koordinator |
| Ihsan Maulana Yusuf | Operator Alat |
| Wan Nashwa Alhasni Yuska | Pencatat Kejadian dan Penjaga Suara |

Pembagian peran tersebut merupakan rencana awal tim, bukan bukti kehadiran anggota pada sesi otomatis.

## B. Persiapan Sebelum Sesi

- [ ] Berkas YAML final sudah disetujui pembimbing.
- [ ] Berkas YAML sudah diserahkan kepada pengelola meja.
- [ ] Mikrofon dan ESP32 diperiksa sebelum sesi.
- [ ] Kipas, pompa, buzzer, dan lampu siap digunakan.
- [ ] Air pompa tersedia dan aman.
- [ ] Ruangan siap untuk pengambilan data.
- [ ] Semua anggota memahami perannya.

Status persiapan fisik sebelum sesi belum dapat diverifikasi dari berkas dataset yang tersedia.

## C. Catatan Pelaksanaan

| Parameter | Keterangan |
|---|---|
| ID sesi | sesi-20261113-200606 |
| Tanggal | 13 November 2026 |
| Waktu mulai berdasarkan ID sesi | 20:06:06 |
| Waktu kondisi terakhir selesai | 21:51:40.906 |
| Waktu log berakhir | 21:51:44.174 |
| Jumlah kondisi direncanakan | 288 |
| Jumlah kondisi aktual | 288 |
| Jumlah kombinasi | 24 |
| Ulangan per kombinasi | 12 |
| Durasi per kondisi | 20 detik |
| Status log | Selesai |

### Catatan Temuan QC

| No. | Kondisi terdampak | Temuan | Tindakan/Keterangan |
|---|---|---|---|
| 1 | Seluruh sesi | Kanal arus pompa tidak tersedia pada daya.csv | Dilakukan pemeriksaan alternatif berbasis energi spektral audio. |
| 2 | Kondisi dengan pompa 200 | Respons energi akustik tidak konsisten pada seluruh pasangan | Ditandai untuk peninjauan, tidak langsung dikeluarkan. |
| 3 | Kondisi dengan kekurangan sampel audio | Kekurangan maksimal 21 sampel per kondisi | Dipertahankan karena kekurangan sampel relatif kecil. |
| 4 | Log sesi | Checksum log.txt berbeda dari manifest asli | Dicatat sebagai keterbatasan integritas log. |
| 5 | Seluruh sesi | Catatan gangguan fisik belum tersedia untuk verifikasi | Memerlukan konfirmasi pengelola meja. |

Temuan di atas merupakan hasil pemeriksaan setelah sesi, bukan catatan pengamatan langsung selama eksperimen.

## D. Pemeriksaan Hasil

- [x] Rekaman audio tersedia sebanyak 106 file WAV.
- [x] Audio menggunakan sample rate 16 kHz.
- [x] Jumlah kondisi sesuai rancangan eksperimen.
- [x] Seluruh kombinasi memiliki 12 ulangan.
- [x] Tidak ditemukan nomor kondisi duplikat.
- [x] Log sesi berakhir dengan tulisan Selesai.
- [x] Pemeriksaan alternatif respons akustik pompa telah dilakukan.
- [x] SHA-256 label.csv dan data_hash telah dihitung ulang.
- [ ] Kesesuaian fisik seluruh aktuator dengan label telah terverifikasi.
- [ ] Gangguan fisik selama sesi telah dikonfirmasi.
- [ ] Hasil pemeriksaan lanjutan telah disetujui pembimbing.
- [ ] Kesamaan data_hash seluruh anggota telah dikonfirmasi.

## E. Kondisi yang Dikeluarkan

| Keterangan | Jumlah |
|---|---:|
| Kondisi awal | 288 |
| Kondisi yang dikeluarkan berdasarkan QC teknis audio | 0 |
| Kondisi yang dipertahankan sementara | 288 |

Tidak ditemukan kerusakan teknis audio yang mengharuskan pengeluaran kondisi secara langsung. Ketidakkonsistenan respons akustik pompa belum cukup untuk memastikan kegagalan aktuator pada kondisi tertentu.

Keputusan akhir mengenai eksklusi berdasarkan gangguan fisik masih memerlukan konfirmasi pengelola meja atau pembimbing.

## F. Bukti Verifikasi

- [Catatan pemeriksaan mutu](../data/CATATAN-SESI.md)
- [Manifest sesi asli](../data/manifest-sesi-20261113-200606.json)
- [Manifest dataset tim](../data/MANIFEST.json)
- [Script verifikasi QC](../src/qc/verifikasi_qc.py)
- [Bukti log sesi](../reports/qc/bukti_log_sesi.txt)
- [Hasil verifikasi](../reports/qc/hasil_verifikasi.txt)
- [Verifikasi kombinasi kondisi](../reports/qc/qc_kombinasi.csv)
- [Pemeriksaan per kondisi](../reports/qc/qc_kondisi.csv)
- [Pemeriksaan respons akustik pompa](../reports/qc/qc_pasangan_pompa.csv)

## G. Kesimpulan

Sesi otomatis telah menghasilkan 288 kondisi sesuai rancangan eksperimen. Pemeriksaan alternatif menunjukkan peningkatan energi akustik pada 21 dari 24 pasangan kondisi pompa terisolasi dengan rata-rata peningkatan sebesar 6,94 dB.

Hasil tersebut mendukung keberadaan respons akustik pompa, tetapi belum memastikan bahwa pompa berfungsi normal pada seluruh kondisi. Seluruh kondisi dipertahankan sementara tanpa perubahan terhadap dataset asli maupun data_hash.
