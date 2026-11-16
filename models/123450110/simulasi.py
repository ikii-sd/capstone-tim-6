import numpy as np
from src.protokol import data


def buat_rekaman(seed: int = 110) -> list[dict]:
    rng = np.random.default_rng(seed)
    rekaman = []

    for kelas in range(data.N_KELAS):
        for ulangan in range(1, data.N_ULANGAN + 1):
            t = np.arange(20 * data.SR) / data.SR
            frekuensi = 300 + kelas * 500

            audio = (
                np.sin(2 * np.pi * frekuensi * t)
                + 0.1 * rng.normal(size=len(t))
            ).astype(np.float32)

            rekaman.append({
                "audio": audio,
                "y": kelas,
                "ulangan": ulangan,
                "kondisi": f"k{kelas}"
            })

    return rekaman