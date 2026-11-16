
import numpy as np

from run import latih_dan_prediksi
from simulasi import buat_rekaman
from src.protokol import data

print("Mulai pengujian integrasi Transformer...")

rekaman = buat_rekaman(seed=110)

print("Jumlah rekaman:", len(rekaman))

pred_val, pred_test = latih_dan_prediksi(
    seed=1,
    final=False,
    rekaman=rekaman,
)

print("Prediksi validasi:", pred_val.shape)
print("Prediksi test:", pred_test)

assert pred_val.ndim == 1
assert len(pred_val) > 0
assert np.all((pred_val >= 0) & (pred_val < data.N_KELAS))

print("INTEGRASI TRANSFORMER BERHASIL")
