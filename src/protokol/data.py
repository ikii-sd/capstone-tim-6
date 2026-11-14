"""Pemuat data kasus tim: taksiran jumlah alat bersuara yang menyala (t06).

Aturan di sini harus sama persis dengan PROTOKOL.md.
Sumber data: folder sesi meja di data/sesi-*/ (label.csv, audio_index.csv, audio/).
"""
from __future__ import annotations

import csv
import itertools
import os
import sys
import wave
from collections.abc import Iterator
from pathlib import Path

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


# Potongan WAV meja tidak bersambung sempurna: batas antar-potongan meleset beberapa sampel
# (buffer perekam). Celah sekecil ini diisi dengan interpolasi linear dan dicatat; celah yang
# lebih panjang dari toleransi ini dianggap data hilang dan membuat pemuatan gagal.
TOLERANSI_CELAH_S = 0.005   # 5 ms = 80 sampel pada 16 kHz

KOLOM_LABEL = ("no", "ulangan", "kipas", "pompa", "buzzer", "lampu", "t_mulai_host")
KOLOM_INDEKS = ("berkas", "t_mulai_host", "sample_rate", "jumlah_sampel")


def _folder_sesi() -> Path:
    """Folder sesi meja: dari variabel lingkungan SESI, atau satu-satunya ``data/sesi-*``."""
    pilih = os.environ.get("SESI")
    if pilih:
        folder = Path(pilih)
        if not folder.is_absolute():
            folder = manifest.AKAR / folder
        if not (folder / "label.csv").exists():
            raise FileNotFoundError(f"SESI={pilih}: {folder / 'label.csv'} tidak ada")
        return folder
    kandidat = sorted(p for p in (manifest.AKAR / "data").glob("sesi-*") if (p / "label.csv").exists())
    if not kandidat:
        raise FileNotFoundError(
            "Folder sesi tidak ditemukan. Letakkan hasil meja di data/sesi-<cap waktu>/ "
            "(berisi label.csv, audio_index.csv, dan audio/), atau setel SESI=<jalur>.")
    if len(kandidat) > 1:
        raise ValueError("Lebih dari satu folder sesi di data/: "
                         + ", ".join(p.name for p in kandidat)
                         + ". Pilih salah satu dengan SESI=<jalur>.")
    return kandidat[0]


def _baca_csv(path: Path, wajib: tuple[str, ...]) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        baris = list(csv.DictReader(f))
    if not baris:
        raise ValueError(f"{path.name} kosong")
    kurang = [k for k in wajib if k not in baris[0]]
    if kurang:
        raise ValueError(f"{path.name}: kolom hilang {kurang}; yang ada {list(baris[0])}")
    return baris


class _Audio:
    """Audio sesi: potongan WAV berurutan waktu, dipetakan lewat ``audio_index.csv``."""

    def __init__(self, folder: Path, cache_maks: int = 3):
        self.folder = folder
        baris = _baca_csv(folder / "audio_index.csv", KOLOM_INDEKS)
        laju = {int(b["sample_rate"]) for b in baris}
        if laju != {SR}:
            raise ValueError(f"audio_index.csv: laju sampel {sorted(laju)}, protokol menuntut {SR} Hz")
        self.seg = sorted((float(b["t_mulai_host"]), int(b["jumlah_sampel"]), b["berkas"]) for b in baris)
        self._cache: dict[str, np.ndarray] = {}
        self._cache_maks = cache_maks
        self.sampel_ditambal = 0

    def _wav(self, nama: str) -> np.ndarray:
        x = self._cache.get(nama)
        if x is None:
            with wave.open(str(self.folder / "audio" / nama), "rb") as w:
                bentuk = (w.getnchannels(), w.getsampwidth(), w.getframerate())
                if bentuk != (1, 2, SR):
                    raise ValueError(f"{nama}: diharapkan mono 16-bit {SR} Hz, ditemukan "
                                     f"{bentuk[0]} kanal / {8 * bentuk[1]} bit / {bentuk[2]} Hz")
                mentah = w.readframes(w.getnframes())
            x = np.frombuffer(mentah, dtype="<i2").astype(np.float32) / 32768.0
            self._cache[nama] = x
            while len(self._cache) > self._cache_maks:
                self._cache.pop(next(iter(self._cache)))
        return x

    def potongan(self, t0: float, n: int) -> np.ndarray:
        """``n`` sampel berurutan mulai waktu host ``t0``; gagal bila ada sampel yang hilang."""
        keluar = np.zeros(n, dtype=np.float32)
        terisi = np.zeros(n, dtype=bool)
        habis = t0 + n / SR
        for t_seg, n_seg, nama in self.seg:
            if t_seg + n_seg / SR <= t0:
                continue
            if t_seg >= habis:
                break
            x = self._wav(nama)
            geser = int(round((t_seg - t0) * SR))
            a_sumber, a_tujuan = max(0, -geser), max(0, geser)
            panjang = min(len(x) - a_sumber, n - a_tujuan)
            if panjang <= 0:
                continue
            keluar[a_tujuan:a_tujuan + panjang] = x[a_sumber:a_sumber + panjang]
            terisi[a_tujuan:a_tujuan + panjang] = True
        if not terisi.all():
            self._tambal(keluar, terisi, t0)
        return keluar

    def _tambal(self, keluar: np.ndarray, terisi: np.ndarray, t0: float) -> None:
        """Isi celah pendek antar-potongan WAV dengan interpolasi linear; celah panjang gagal."""
        batas = np.flatnonzero(np.diff(np.concatenate(([0], (~terisi).view(np.int8), [0]))))
        maks = int(TOLERANSI_CELAH_S * SR)
        for awal, akhir in zip(batas[::2], batas[1::2]):
            if akhir - awal > maks:
                raise ValueError(
                    f"audio hilang pada t_mulai_host={t0:.4f}: {akhir - awal} sampel berurutan "
                    f"({(akhir - awal) / SR * 1000:.1f} ms) melebihi toleransi "
                    f"{TOLERANSI_CELAH_S * 1000:.0f} ms; periksa audio_index.csv dan audio/")
        kosong = np.flatnonzero(~terisi)
        ada = np.flatnonzero(terisi)
        keluar[kosong] = np.interp(kosong, ada, keluar[ada]).astype(np.float32)
        self.sampel_ditambal += int(kosong.size)


def _baca_sesi() -> Iterator[dict]:
    """Rekaman dari folder sesi meja, satu per kondisi (288 = 24 kombinasi x 12 ulangan).

    Audio meja direkam sebagai potongan WAV berurutan, bukan satu berkas per kondisi, sehingga
    tiap kondisi diiris dari garis waktu ``t_mulai_host`` dengan bantuan ``audio_index.csv``.
    Menghasilkan {"audio": array 1D (20 detik), "y": int 0..3, "ulangan": int, "kondisi": str}.
    """
    folder = _folder_sesi()
    audio = _Audio(folder)
    baris = _baca_csv(folder / "label.csv", KOLOM_LABEL)
    baris.sort(key=lambda b: float(b["t_mulai_host"]))
    n = DURASI_S * SR
    for b in baris:
        kipas, pompa, buzzer, lampu = (int(b[k]) for k in ("kipas", "pompa", "buzzer", "lampu"))
        yield {"audio": audio.potongan(float(b["t_mulai_host"]), n),
               "y": label_dari_faktor(kipas, pompa, buzzer, lampu),
               "ulangan": int(b["ulangan"]),
               "kondisi": f"k{kipas}-p{pompa}-b{buzzer}-l{lampu}"}
    if audio.sampel_ditambal:
        print(f"catatan: {audio.sampel_ditambal} sampel "
              f"({audio.sampel_ditambal / SR * 1000:.1f} ms dari {len(baris) * DURASI_S} detik) "
              f"diisi interpolasi pada batas potongan WAV.", file=sys.stderr, flush=True)


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
    Bila variabel lingkungan DATA_SINTETIS=1, memakai rekaman PALSU (hanya untuk uji alur).
    """
    if rekaman is None:
        if os.environ.get("DATA_SINTETIS") == "1":
            n_kondisi = int(os.environ.get("KONDISI_SINTETIS", "8"))
            print("PERINGATAN: DATA_SINTETIS=1, memakai rekaman PALSU. Hasilnya bukan evaluasi.",
                  file=sys.stderr, flush=True)
            rekaman = rekaman_sintetis(n_kondisi)
        else:
            rekaman = _baca_sesi()

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