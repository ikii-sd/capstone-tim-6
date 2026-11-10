"""Pemuat data kasus tim: taksiran jumlah alat bersuara yang menyala (t06).

DRAF Sprint 0. Aturan di sini harus sama persis dengan PROTOKOL.md.
Bagian bertanda TODO bergantung pada format folder sesi (audio + label).
"""
from __future__ import annotations

import itertools

import numpy as np

from src.common import manifest, split

TUGAS = "klasifikasi"  # jumlah alat bersuara: 0, 1, 2, 3

SR = 16_000        # Hz
DURASI_S = 20      # durasi satu kondisi (detik)
JENDELA_S = 2      # panjang jendela (detik)
GESER_S = 1        # geseran jendela (detik)
BUANG_AWAL_S = 1   # detik pertama tiap kondisi dibuang
N_ULANGAN = 12
N_LIPATAN = 3      # 12 ulangan -> 3 lipatan @ 4 ulangan
SEED = 2026
N_KELAS = 4        # jumlah alat bersuara: 0, 1, 2, 3

# Log-mel (masukan model sesuai rencana t06: log-mel 64 pita, 2 detik)
N_MEL = 64
N_FFT = 1024
HOP = 320          # 20 ms -> 101 bingkai per jendela 2 detik
FMIN, FMAX = 0.0, 8000.0


def potong(audio, sr: int = SR) -> np.ndarray:
    """Satu rekaman kondisi (1D) -> jendela berukuran (n_jendela, sr * JENDELA_S)."""
    audio = np.asarray(audio, dtype=np.float32)[BUANG_AWAL_S * sr:]
    panjang, langkah = JENDELA_S * sr, GESER_S * sr
    if len(audio) < panjang:
        return np.empty((0, panjang), dtype=np.float32)
    n = (len(audio) - panjang) // langkah + 1
    idx = np.arange(n)[:, None] * langkah + np.arange(panjang)[None, :]
    return audio[idx]


def _bank_mel(sr: int = SR) -> np.ndarray:
    """Filter segitiga skala mel (HTK): bentuk (N_MEL, N_FFT // 2 + 1)."""
    def hz_ke_mel(f):
        return 2595.0 * np.log10(1.0 + np.asarray(f) / 700.0)

    def mel_ke_hz(m):
        return 700.0 * (10.0 ** (np.asarray(m) / 2595.0) - 1.0)

    titik = mel_ke_hz(np.linspace(hz_ke_mel(FMIN), hz_ke_mel(FMAX), N_MEL + 2))
    freq = np.linspace(0, sr / 2, N_FFT // 2 + 1)
    bank = np.zeros((N_MEL, len(freq)), dtype=np.float32)
    for i in range(N_MEL):
        kiri, tengah, kanan = titik[i], titik[i + 1], titik[i + 2]
        naik = (freq - kiri) / (tengah - kiri)
        turun = (kanan - freq) / (kanan - tengah)
        bank[i] = np.maximum(0.0, np.minimum(naik, turun))
    return bank


_BANK = None


def log_mel(jendela, sr: int = SR) -> np.ndarray:
    """Jendela (n, sr * JENDELA_S) -> log-mel (n, N_MEL, n_bingkai)."""
    global _BANK
    if _BANK is None:
        _BANK = _bank_mel(sr)
    x = np.asarray(jendela, dtype=np.float32)
    pad = N_FFT // 2
    x = np.pad(x, ((0, 0), (pad, pad)), mode="reflect")
    n_bingkai = 1 + (x.shape[1] - N_FFT) // HOP
    idx = np.arange(n_bingkai)[:, None] * HOP + np.arange(N_FFT)[None, :]
    bingkai = x[:, idx] * np.hanning(N_FFT).astype(np.float32)   # (n, T, N_FFT)
    daya = np.abs(np.fft.rfft(bingkai, axis=-1)) ** 2            # (n, T, F)
    mel = daya @ _BANK.T                                         # (n, T, N_MEL)
    return np.log(mel + 1e-6).transpose(0, 2, 1).astype(np.float32)


def bagi_ulangan(ulangan_ids, lipatan: int = 0, seed: int = SEED):
    """Bagi ulangan menjadi (latih, validasi, uji). Satuan pemisahan = ulangan.

    Uji   : 1 lipatan (4 ulangan), lipatan diacak tetap dengan seed 2026.
    Latih/validasi: sisa ulangan dibagi memakai src.common.split (split beku).
    """
    ids = np.array(sorted(set(int(i) for i in ulangan_ids)))
    if len(ids) != N_ULANGAN:
        raise ValueError(f"Diharapkan {N_ULANGAN} ulangan, ditemukan {len(ids)}: {ids.tolist()}")
    acak = np.random.default_rng(seed).permutation(ids).reshape(N_LIPATAN, -1)
    uji = [int(i) for i in acak[lipatan]]
    sisa = np.array(sorted(int(i) for k in range(N_LIPATAN) if k != lipatan for i in acak[k]))
    tr, va = split.indeks(len(sisa))
    if len(tr) == 0 or len(va) == 0:
        raise ValueError("split.indeks menghasilkan bagian kosong pada tingkat ulangan")
    return [int(i) for i in sisa[tr]], [int(i) for i in sisa[va]], uji


def periksa_kebocoran(g_latih, g_val, g_uji) -> None:
    """Gagal bila satu ulangan muncul di lebih dari satu bagian."""
    a, b, c = set(g_latih.tolist()), set(g_val.tolist()), set(g_uji.tolist())
    tumpang = (a & b) | (a & c) | (b & c)
    if tumpang:
        raise AssertionError(f"Ulangan muncul di lebih dari satu bagian: {sorted(tumpang)}")


def _baca_sesi() -> list[dict]:
    """TODO: baca folder sesi (audio/ 16 kHz + label dari relay), lewat manifest.

    Harus mengembalikan daftar rekaman, satu per (kondisi, ulangan):
        {"audio": array 1D (20 detik), "y": int 0..3, "ulangan": int, "kondisi": str}
    """
    raise NotImplementedError("Isi _baca_sesi() setelah format folder sesi diketahui.")


FAKTOR = {"kipas": (0, 128, 255), "pompa": (0, 200), "buzzer": (0, 1), "lampu": (0, 255)}


def label_dari_faktor(kipas, pompa, buzzer, lampu=0) -> int:
    """Jumlah alat bersuara: kipas > 0, pompa > 0, buzzer = 1. Lampu tidak dihitung."""
    return int(kipas > 0) + int(pompa > 0) + int(buzzer == 1)


def rekaman_sintetis(kondisi_per_ulangan: int = 24, seed: int = 0):
    """Generator rekaman PALSU untuk uji bentuk dan arsitektur model.

    BUKAN data resmi: hasilnya tidak boleh dilaporkan sebagai evaluasi.
    Tiap alat bersuara menambah satu nada (kipas 300 Hz, pompa 700 Hz, buzzer 2000 Hz).
    """
    semua = list(itertools.product(*FAKTOR.values()))
    semua.sort(key=lambda f: label_dari_faktor(*f))
    n = min(kondisi_per_ulangan, len(semua))
    pilih = sorted(set(np.linspace(0, len(semua) - 1, n).round().astype(int)))
    kondisi = [semua[i] for i in pilih]
    rng = np.random.default_rng(seed)
    t = np.arange(DURASI_S * SR) / SR
    for ulangan in range(1, N_ULANGAN + 1):
        for kipas, pompa, buzzer, lampu in kondisi:
            audio = 0.05 * rng.normal(size=t.size)
            if kipas > 0:
                audio += 0.3 * np.sin(2 * np.pi * 300 * t)
            if pompa > 0:
                audio += 0.3 * np.sin(2 * np.pi * 700 * t)
            if buzzer == 1:
                audio += 0.3 * np.sin(2 * np.pi * 2000 * t)
            yield {"audio": audio.astype(np.float32),
                   "y": label_dari_faktor(kipas, pompa, buzzer, lampu),
                   "ulangan": ulangan,
                   "kondisi": f"k{kipas}-p{pompa}-b{buzzer}-l{lampu}"}


def muat_sintetis(lipatan: int = 0, kondisi_per_ulangan: int = 24):
    """Seperti muat(), tetapi memakai rekaman PALSU. Hanya untuk uji lokal, jangan di-commit ke run.py."""
    return muat(lipatan=lipatan, rekaman=rekaman_sintetis(kondisi_per_ulangan))


def muat(lipatan: int = 0, rekaman: list[dict] | None = None):
    """Kembalikan X_train, y_train, X_val, y_val, X_test, y_test.

    X berbentuk (N, N_MEL, n_bingkai) = log-mel ternormalisasi; y = jumlah alat bersuara.
    """
    rekaman = _baca_sesi() if rekaman is None else rekaman

    X, y, g = [], [], []
    for r in rekaman:
        w = potong(r["audio"])
        if len(w) == 0:
            continue
        X.append(log_mel(w))
        y += [r["y"]] * len(w)
        g += [r["ulangan"]] * len(w)
    X = np.concatenate(X)
    y = np.array(y, dtype=np.int64)
    g = np.array(g)
    assert len(X) == len(y) == len(g), "ukuran X/y/grup tidak konsisten"
    assert y.min() >= 0 and y.max() <= N_KELAS - 1, "label di luar 0..3"

    id_latih, id_val, id_uji = bagi_ulangan(g, lipatan)
    m_latih, m_val, m_uji = (np.isin(g, ids) for ids in (id_latih, id_val, id_uji))
    periksa_kebocoran(g[m_latih], g[m_val], g[m_uji])

    # Normalisasi per pita mel, dihitung dari data latih saja.
    rerata = X[m_latih].mean(axis=(0, 2), keepdims=True)
    simpang = X[m_latih].std(axis=(0, 2), keepdims=True) + 1e-6

    def norm(a):
        return ((a - rerata) / simpang).astype(np.float32)

    return (norm(X[m_latih]), y[m_latih],
            norm(X[m_val]), y[m_val],
            norm(X[m_uji]), y[m_uji])