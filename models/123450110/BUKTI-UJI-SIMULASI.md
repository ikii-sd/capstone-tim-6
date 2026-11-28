# Bukti Uji Simulasi Transformer

## 1. Tujuan

Pengujian dilakukan untuk memastikan runner Transformer dapat menjalankan proses training menggunakan data sintetis dan memastikan bentuk input serta output model sesuai dengan rancangan.

## 2. Pengujian Runner

**Perintah:**
```bash
DATA_SINTETIS=1 python models/123450110/run.py --seed 1 --fold 0
```

**Hasil pengujian:**
- Data latih: (1008, 64, 101)
- Data validasi: (144, 64, 101)
- Data pengujian: (576, 64, 101)
- Loss epoch 1: 0.4768
- Loss epoch 2: 0.0433
- Durasi: 23.95 detik
- Bentuk prediksi validasi: (144,)
- Status: Training selesai tanpa error.

## 3. Pengujian Forward Pass

**Bentuk input:** (2, 64, 101)

**Bentuk output:** (2, 4)

**Prediksi kelas contoh:** [1, 1]

**Jumlah kelas:** 4

Model menerima dua sampel dengan 64 kanal mel dan 101 frame, kemudian menghasilkan empat skor kelas untuk setiap sampel.

## 4. Kesimpulan

Runner berhasil menjalankan training menggunakan data sintetis selama dua epoch. Pengujian forward pass menunjukkan bahwa model menerima input berbentuk (B, 64, 101) dan menghasilkan output berbentuk (B, 4).

Pengujian ini merupakan verifikasi alur dan bentuk data, bukan evaluasi performa pada data primer. Hasil metrik simulasi tidak digunakan sebagai hasil evaluasi resmi.