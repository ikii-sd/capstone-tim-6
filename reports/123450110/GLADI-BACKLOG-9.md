# Laporan Pemeriksaan Gladi Rencana — Backlog #9

**Tim:** 6  
**PIC:** Ihsan Maulana Yusuf (123450110)  
**Tanggal:** 28 November 2026  
**Rencana:** `rencana/t06-hitung-alat-suara.yaml`

## 1. Tujuan

Memeriksa kesiapan konfigurasi rencana eksperimen Tim 6 untuk pengambilan data meja uji, termasuk jumlah kombinasi, jumlah ulangan, durasi eksperimen, serta ketersediaan bukti pelaksanaan sesi.

## 2. Pemeriksaan Konfigurasi

Rencana eksperimen menggunakan:

- Kipas: 0, 128, 255
- Pompa: 0, 200
- Buzzer: 0, 1
- Lampu: 0, 255
- Ulangan: 12
- Durasi kondisi: 20 detik
- Jeda: 2 detik
- Audio: aktif, 16.000 Hz

Perhitungan kondisi:

3 × 2 × 2 × 2 × 12 = **288 kondisi**.

Estimasi waktu:

288 × (20 + 2) = **6.336 detik**, atau sekitar **1 jam 45 menit 36 detik**.

## 3. Pengujian Konfigurasi

Perintah:

```bash
python reports/123450110/periksa_rencana_meja.py
```

Hasil:

- Kombinasi: 24
- Ulangan: 12
- Total kondisi: 288
- Estimasi: 105,60 menit
- Status pemeriksaan: PASS

Bukti pengujian tersedia pada:

`reports/123450110/HASIL-PEMERIKSAAN-RENCANA.txt`

## 4. Bukti Riwayat Eksperimen

Berdasarkan riwayat Ruang Cerdas 5 Volt, terdapat tiga sesi Tim 6 pada 13 November 2026:

| Mulai | Kondisi | Status |
|---|---|---|
| 17.43 WIB | 5/288 | Dibatalkan |
| 18.08 WIB | 288/288 | Selesai |
| 20.06 WIB | 288/288 | Selesai |

Riwayat tersebut mendukung bahwa rencana telah dilaksanakan pada meja uji.

## 5. Keterbatasan

File `meja.py` tidak ditemukan pada repository Tim 6 yang diperiksa.

Skrip `periksa_rencana_meja.py` melakukan validasi konfigurasi secara mandiri, bukan menjalankan simulator resmi meja.

Dengan demikian, bukti pelaksanaan sesi nyata dan pemeriksaan rencana telah tersedia, tetapi eksekusi mode simulasi resmi belum dapat diverifikasi.

## 6. Kesimpulan

Konfigurasi eksperimen Tim 6 berhasil diverifikasi dengan hasil PASS, mencakup 288 kondisi dan estimasi durasi sekitar 1 jam 46 menit.

Riwayat Ruang Cerdas mencatat dua sesi eksperimen selesai dengan 288/288 kondisi.

Dokumen ini menjadi bukti pemeriksaan rencana dan kesiapan pelaksanaan, dengan keterbatasan pada ketersediaan bukti mode simulasi resmi.