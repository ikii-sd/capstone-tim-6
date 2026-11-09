
import numpy as np

from run import latih_dan_prediksi
from src.protokol import data

# Data sintetis: 4 kondisi x 12 ulangan
rng = np.random.default_rng(110)

rekaman = []

for kelas in range(data.N_KELAS):
    for ulangan in range(1, data.N_ULANGAN + 1):
        t = np.arange(20 * data.SR) / data.SR

        # Sinyal simulasi berbeda untuk setiap kelas
        frekuensi = 300 + kelas * 500
        audio = (
            np.sin(2 * np.pi * frekuensi * t)
            + 0.1 * rng.normal(size=len(t))
        ).astype(np.float32)

        rekaman.append({
            "audio": audio,
            "y": kelas,
            "ulangan": ulangan,
            "kondisi": f"k{kelas}",
        })

print("Mulai pengujian integrasi Transformer...")

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
