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

# 7) Variabel lingkungan DATA_SINTETIS=1 membuat muat() tanpa argumen memakai data palsu
#    (dipakai run.py dan evaluate.py lewat subproses), dan deterministik antar-panggilan.
import os

os.environ["DATA_SINTETIS"] = "1"
os.environ["KONDISI_SINTETIS"] = "4"
a1 = data.muat()
a2 = data.muat()
del os.environ["DATA_SINTETIS"], os.environ["KONDISI_SINTETIS"]
assert a1[0].shape[1:] == (data.N_MEL, 101)
assert all(np.array_equal(x, y_) for x, y_ in zip(a1, a2)), "muat() sintetis tidak deterministik"
# 7b) Tanpa DATA_SINTETIS, muat() memakai folder sesi meja. Bila folder sesi belum ada,
#     kegagalannya harus jelas, bukan diam-diam memakai data palsu.
try:
    folder_sesi = data._folder_sesi()
except FileNotFoundError as e:
    folder_sesi = None
    print("folder sesi belum ada; pesan:", str(e).split(".")[0])
if folder_sesi is not None:
    print("folder sesi:", folder_sesi.name)
    Xl, yl, Xv, yv, Xu, yu = data.muat()
    n_l, n_v, n_u = len(yl), len(yv), len(yu)
    total = n_l + n_v + n_u
    print("data meja latih/val/uji:", n_l, n_v, n_u, "| bentuk X:", Xl.shape[1:])
    assert Xl.shape[1:] == (data.N_MEL, 101)
    per_kondisi = (data.DURASI_S - data.BUANG_AWAL_S - data.JENDELA_S) // data.GESER_S + 1
    assert total % per_kondisi == 0, "jumlah jendela bukan kelipatan jendela per kondisi"
    assert n_u == 4 * total // data.N_ULANGAN, "uji bukan 4 dari 12 ulangan"
    assert abs(float(Xl.mean())) < 1e-3 and abs(float(Xl.std()) - 1) < 1e-2

# 8) Pemotong audio sesi: potongan WAV berurutan diiris memakai t_mulai_host.
import csv
import tempfile
import wave
from pathlib import Path

SR = data.SR
L = 15 * data.SR                       # satu potongan WAV = 15 detik
T0 = 1_700_000_000.0
SINYAL = ((np.arange(3 * L) % 2000) - 1000).astype("<i2")
HARAP = SINYAL[10 * SR:30 * SR].astype(np.float32) / 32768.0


def sesi_palsu(akar, geser_sampel=0):
    """Tiga potongan WAV berurutan; potongan ke-2 dan ke-3 digeser untuk meniru celah perekam.

    Satu kondisi 20 detik dimulai pada detik ke-10, sehingga melintasi batas potongan.
    """
    folder = Path(akar)
    (folder / "audio").mkdir(parents=True)
    baris = []
    for j in range(3):
        nama = f"audio-{j + 1:04d}.wav"
        with wave.open(str(folder / "audio" / nama), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(SINYAL[j * L:(j + 1) * L].tobytes())
        t = T0 + j * L / SR + (geser_sampel / SR if j >= 1 else 0.0)
        baris.append({"berkas": nama, "t_mulai_host": f"{t:.6f}",
                      "sample_rate": SR, "jumlah_sampel": L})
    with (folder / "audio_index.csv").open("w", newline="", encoding="utf-8") as f:
        tulis = csv.DictWriter(f, ["berkas", "t_mulai_host", "sample_rate", "jumlah_sampel"])
        tulis.writeheader()
        tulis.writerows(baris)
    with (folder / "label.csv").open("w", newline="", encoding="utf-8") as f:
        tulis = csv.DictWriter(f, ["no", "ulangan", "kipas", "pompa", "buzzer", "lampu",
                                   "t_mulai_host"])
        tulis.writeheader()
        tulis.writerow({"no": 1, "ulangan": 1, "kipas": 128, "pompa": 0, "buzzer": 1,
                        "lampu": 255, "t_mulai_host": f"{T0 + 10:.6f}"})
    return folder


with tempfile.TemporaryDirectory() as d:
    folder = sesi_palsu(d)
    au = data._Audio(folder)
    irisan = au.potongan(T0 + 10, 20 * SR)
    assert irisan.shape == (20 * SR,) and irisan.dtype == np.float32
    assert np.array_equal(irisan, HARAP), "irisan audio tidak sejajar dengan t_mulai_host"
    assert au.sampel_ditambal == 0
    print("irisan melintasi batas potongan: tepat sampel demi sampel")

    # _baca_sesi() lewat SESI: label dan ulangan ikut terbaca.
    os.environ["SESI"] = str(folder)
    (rekaman,) = list(data._baca_sesi())
    del os.environ["SESI"]
    assert rekaman["y"] == data.label_dari_faktor(128, 0, 1, 255) == 2
    assert rekaman["ulangan"] == 1 and rekaman["audio"].shape == (data.DURASI_S * SR,)
    assert len(data.potong(rekaman["audio"])) == 18
    print("_baca_sesi() pada sesi palsu:", rekaman["kondisi"], "-> y =", rekaman["y"])

with tempfile.TemporaryDirectory() as d:
    au = data._Audio(sesi_palsu(d, geser_sampel=5))      # celah 5 sampel, di bawah toleransi
    irisan = au.potongan(T0 + 10, 20 * SR)
    assert au.sampel_ditambal == 5, au.sampel_ditambal
    # Potongan ke-2 mulai 5 sampel lebih lambat, jadi isinya juga bergeser 5 sampel:
    # sebelum batas tetap tepat, 5 sampel di celah ditambal, sesudahnya tepat pada posisi barunya.
    assert np.array_equal(irisan[:5 * SR], HARAP[:5 * SR]), "bagian sebelum celah bergeser"
    ekor = SINYAL[L:L + 15 * SR - 5].astype(np.float32) / 32768.0
    assert np.array_equal(irisan[5 * SR + 5:], ekor), "bagian sesudah celah tidak sejajar"
    tambalan = irisan[5 * SR:5 * SR + 5]
    batas_bawah = min(irisan[5 * SR - 1], irisan[5 * SR + 5])
    batas_atas = max(irisan[5 * SR - 1], irisan[5 * SR + 5])
    assert np.isfinite(tambalan).all()
    assert (tambalan >= batas_bawah - 1e-6).all() and (tambalan <= batas_atas + 1e-6).all()
    print("celah 5 sampel ditambal interpolasi; sisanya sejajar dengan t_mulai_host")

with tempfile.TemporaryDirectory() as d:
    terlalu = int(data.TOLERANSI_CELAH_S * SR) + 20     # celah di atas toleransi
    au = data._Audio(sesi_palsu(d, geser_sampel=terlalu))
    try:
        au.potongan(T0 + 10, 20 * SR)
        raise SystemExit("GAGAL: celah besar tidak terdeteksi")
    except ValueError as e:
        assert "melebihi toleransi" in str(e)
        print("celah besar ditolak:", str(e)[:64], "...")

# 8b) Kolom wajib yang hilang harus ditolak dengan pesan yang menyebut kolom itu.
with tempfile.TemporaryDirectory() as d:
    folder = sesi_palsu(d)
    berkas = folder / "label.csv"
    berkas.write_text(berkas.read_text(encoding="utf-8").replace("ulangan", "ulang", 1),
                      encoding="utf-8")
    try:
        data._baca_csv(berkas, data.KOLOM_LABEL)
        raise SystemExit("GAGAL: kolom hilang tidak terdeteksi")
    except ValueError as e:
        assert "ulangan" in str(e)
        print("kolom label hilang ditolak:", str(e)[:56], "...")

print("SEMUA UJI LULUS")