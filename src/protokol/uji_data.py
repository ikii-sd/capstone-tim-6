"""Uji aturan protokol pada audio palsu. Jalankan dari akar repo:

    python -m src.protokol.uji_data
"""
import numpy as np

from src.protokol import data

rng = np.random.default_rng(0)

# 1) Satu kondisi 20 detik -> 18 jendela; 1 detik pertama (nilai 1000) tidak boleh ikut.
audio = rng.normal(size=20 * data.SR).astype(np.float32)
audio[: data.SR] = 1000.0
w = data.potong(audio)
print("bentuk jendela:", w.shape)
assert w.shape == (18, 2 * data.SR)
assert w.max() < 500, "detik pertama bocor ke jendela"

# 1b) Jendela tidak melewati batas kondisi: tiap jendela adalah irisan lurus dari detik 1..20.
urut = np.arange(20 * data.SR, dtype=np.float32)
wu = data.potong(urut)
for i in range(len(wu)):
    awal = data.BUANG_AWAL_S * data.SR + i * data.GESER_S * data.SR
    assert wu[i, 0] == awal and wu[i, -1] == awal + 2 * data.SR - 1
    assert wu[i, -1] <= 20 * data.SR - 1
assert len(wu) == 18
print("batas jendela aman")

# 2) Log-mel: bentuk benar, nilai hingga, dan nada 1 kHz jatuh di pita mel yang tepat.
t = np.arange(2 * data.SR) / data.SR
nada = np.sin(2 * np.pi * 1000 * t).astype(np.float32)[None, :]
lm = data.log_mel(nada)
print("bentuk log-mel:", lm.shape)
assert lm.shape == (1, data.N_MEL, 101)
assert np.isfinite(lm).all()
assert np.isfinite(data.log_mel(np.zeros((1, 2 * data.SR), dtype=np.float32))).all()
mel_1k = 2595 * np.log10(1 + 1000 / 700)
mel_maks = 2595 * np.log10(1 + data.FMAX / 700)
pita_harap = mel_1k / mel_maks * (data.N_MEL + 1) - 1
pita = int(lm[0].mean(axis=1).argmax())
print("pita puncak:", pita, "diharapkan sekitar", round(pita_harap, 1))
assert abs(pita - pita_harap) <= 2

# 3) Rekaman palsu: 4 kondisi x 12 ulangan.
rekaman = [
    {"audio": rng.normal(loc=k, size=20 * data.SR).astype(np.float32),
     "y": k, "ulangan": u, "kondisi": f"k{k}"}
    for k in range(4) for u in range(1, 13)
]
Xl, yl, Xv, yv, Xu, yu = data.muat(lipatan=0, rekaman=rekaman)
n_l, n_v, n_u = Xl.shape[0], Xv.shape[0], Xu.shape[0]
print("latih/val/uji:", n_l, n_v, n_u, "| bentuk X:", Xl.shape[1:])
assert Xl.shape[1:] == (data.N_MEL, 101)
assert n_u == 4 * 4 * 18
assert n_l + n_v + n_u == 4 * 12 * 18
assert n_l > 0 and n_v > 0
print("rerata/simpangan latih:", round(float(Xl.mean()), 4), round(float(Xl.std()), 4))
assert abs(Xl.mean()) < 1e-3 and abs(Xl.std() - 1) < 1e-2

# 4) Ketiga lipatan: uji saling lepas dan menutup 12 ulangan; latih/val/uji tidak beririsan.
uji_semua = []
for f in range(3):
    l, v, u = data.bagi_ulangan(range(1, 13), f)
    assert not (set(l) & set(v)) and not (set(l) & set(u)) and not (set(v) & set(u))
    assert sorted(l + v + u) == list(range(1, 13))
    uji_semua += u
assert sorted(uji_semua) == list(range(1, 13))
print("lipatan uji:", [data.bagi_ulangan(range(1, 13), f)[2] for f in range(3)])

# 4b) Label di luar 0..3 harus ditolak.
buruk = [dict(r) for r in rekaman]
buruk[0]["y"] = 5
try:
    data.muat(rekaman=buruk)
    raise SystemExit("GAGAL: label 5 tidak ditolak")
except AssertionError as e:
    print("label buruk ditolak:", e)

# 5) Cek kebocoran harus benar-benar gagal pada kasus buruk.
try:
    data.periksa_kebocoran(np.array([1, 2]), np.array([3]), np.array([2, 4]))
    raise SystemExit("GAGAL: kebocoran tidak terdeteksi")
except AssertionError as e:
    print("kebocoran terdeteksi:", e)

# 6) Data sintetis untuk rekan tim: bentuk benar, semua kelas ada, label sesuai aturan.
import collections
import time

hitung = collections.Counter(
    data.label_dari_faktor(*f) for f in __import__("itertools").product(*data.FAKTOR.values())
)
assert dict(sorted(hitung.items())) == {0: 2, 1: 8, 2: 10, 3: 4}
mulai = time.time()
Xl, yl, Xv, yv, Xu, yu = data.muat_sintetis(kondisi_per_ulangan=8)
print("sintetis (8 kondisi):", Xl.shape, Xv.shape, Xu.shape, f"{time.time() - mulai:.1f} dtk")
assert Xl.shape[1:] == (data.N_MEL, 101) and Xl.dtype == np.float32 and yl.dtype == np.int64
assert set(np.concatenate([yl, yv, yu]).tolist()) == {0, 1, 2, 3}
assert Xu.shape[0] == 4 * 8 * 18

print("SEMUA UJI LULUS")