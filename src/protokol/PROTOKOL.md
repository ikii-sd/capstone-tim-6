# Protokol evaluasi tim — Tim 6

Diisi Penjaga Data & Evaluasi pada Sprint 0, digabung ke `main` lewat *pull request* yang
disetujui pembimbing, lalu **dibekukan**. Perubahan setelah itu hanya lewat *pull request*
baru yang disetujui pembimbing.

| Butir | Isi |
|---|---|
| Kasus (dari kartu Kasus tim) | Taksiran jumlah alat bersuara yang menyala (t06) |
| Sumber dataset | Rencana: `rencana/t06-hitung-alat-suara.yaml` (seed 1006, 12 ulangan, kondisi 20 detik, jeda 2 detik). Sementara memakai data simulasi; data meja asli tersedia sekitar 10 Nov, lalu `data/MANIFEST.json` diperbarui lewat *pull request* yang disetujui pembimbing (`data_hash` akan berubah). Tautan: … |
| Jenis tugas (`TUGAS`) | klasifikasi (jumlah alat bersuara 0–3) |
| Target / label | jumlah aktuator bersuara (kipas, pompa, buzzer) dari relay, otomatis; lampu pengecoh tidak dihitung |
| Ukuran data latih / validasi / uji | Per ulangan: 7 / 1 / 4 dari 12 ulangan. 18 jendela per kondisi. Jumlah jendela: … / … / … (diisi setelah data jadi) |
| Cara split | Satuan pemisahan = **ulangan**: semua jendela dari satu ulangan berada di satu bagian (jendela saling tumpang tindih 1 detik). 12 ulangan dibagi 3 lipatan @ 4 ulangan (acak tetap, seed 2026); uji = 1 lipatan. Sisa 8 ulangan dibagi dengan `split.indeks` seed 2026, porsi validasi bawaan 10 % → 7 latih, 1 validasi. `muat()` gagal otomatis bila ada ulangan di lebih dari satu bagian. |
| Metrik utama untuk komparasi |  dan AkurasiMAE (selisih jumlah alat prediksi dan sebenarnya) |
| Praproses yang sama untuk semua model | Audio 16 kHz dari `audio/`; buang 1 detik pertama tiap kondisi (20 detik); jendela 2 detik bergeser 1 detik (18 jendela per kondisi); log-mel 64 pita (FFT 1024, geseran 320 sampel, 0–8000 Hz) → bentuk (64, 101); normalisasi per pita mel dari data latih saja |
| Anggaran komputasi per run | ≤ 20 menit CPU laptop (atau yang disetujui pembimbing) |
| Evaluasi data uji | sekali, oleh Penjaga Data, pada sprint terakhir (`--final`) |
| `data_hash` saat dibekukan | … (dari `results/baseline/metrics.json`) |

Disetujui pembimbing pada: … (tautan *pull request*)