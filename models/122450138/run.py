"""Transfer Learning PANNs Cnn6 untuk klasifikasi audio Tim 6."""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

AKAR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AKAR))
from src.protokol import data  # noqa: E402  (protokol tim yang dibekukan)

NIM = Path(__file__).resolve().parent.name     # nama folder = NIM
JALUR = "tl"


def latih_dan_prediksi(seed: int, final: bool) -> tuple[np.ndarray, np.ndarray | None]:
    """Latih classifier pada embedding PANNs dan prediksi kelas 0 sampai 3."""
    import torch

    from model import PannsCnn6, TLClassifierHead

    torch.manual_seed(seed)
    np.random.seed(seed)
    Xtr, ytr, Xva, _, Xte, _ = data.muat()

    backbone = PannsCnn6.pralatih()

    @torch.no_grad()
    def embedding(fitur):
        x = torch.as_tensor(fitur, dtype=torch.float32)
        return torch.cat([backbone(batch) for batch in x.split(32)])

    # Ekstraksi cukup sekali per split karena backbone dibekukan.
    X = embedding(Xtr)
    y = torch.as_tensor(ytr, dtype=torch.long)
    model = TLClassifierHead(backbone.dim_embedding)
    opt = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.01)
    for _ in range(10):
        for idx in torch.randperm(len(X)).split(128):
            opt.zero_grad()
            loss = torch.nn.functional.cross_entropy(model(X[idx]), y[idx])
            loss.backward()
            opt.step()

    model.eval()
    with torch.no_grad():
        pred_val = model(embedding(Xva)).argmax(1).numpy()
        pred_test = model(embedding(Xte)).argmax(1).numpy() if final and Xte is not None else None
    return pred_val, pred_test


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--final", action="store_true", help="sprint terakhir: evaluasi data uji sekali")
    ap.add_argument("--perangkat", default="cpu laptop")
    a = ap.parse_args()
    t0 = time.time()
    pred_val, pred_test = latih_dan_prediksi(a.seed, a.final)
    durasi = time.time() - t0
    out = AKAR / "results" / NIM
    out.mkdir(parents=True, exist_ok=True)
    np.save(out / "pred_val.npy", np.asarray(pred_val))
    perintah = [sys.executable, "-m", "src.common.evaluate", "--nim", NIM, "--model", JALUR, "--seed", str(a.seed),
                "--pred-val", str(out / "pred_val.npy"), "--durasi", f"{durasi:.1f}", "--perangkat", a.perangkat]
    if pred_test is not None:
        np.save(out / "pred_test.npy", np.asarray(pred_test))
        perintah += ["--pred-test", str(out / "pred_test.npy")]
    subprocess.run(perintah, check=True, cwd=AKAR)


if __name__ == "__main__":
    main()
