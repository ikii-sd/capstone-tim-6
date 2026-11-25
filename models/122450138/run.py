"""Transfer Learning PANNs Cnn6 untuk klasifikasi audio Tim 6 (0..3 alat bersuara).

    python models/122450138/run.py --seed 1 [--final]

Opsi tambahan untuk pencarian hyperparameter, ablation, dan smoke test:
    python models/122450138/run.py --smoke-test
    python models/122450138/run.py --seed 1 --freeze-blocks 4
    python models/122450138/run.py --seed 1 --dropout 0.0 --wd 0.0
    python models/122450138/run.py --seed 1 --freeze-blocks 4 --tanpa-norm-emb
"""
# Model milik 122450138 (Ahmad Rizqi) — Backlog #13 Transfer Learning
from __future__ import annotations

import argparse
import copy
import csv
import json
import hashlib
import os
import shutil
import tempfile
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

AKAR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AKAR))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.common import manifest, split  # noqa: E402
from src.protokol import data  # noqa: E402  (protokol tim yang dibekukan)

NIM = Path(__file__).resolve().parent.name     # nama folder = NIM (122450138)
JALUR = "tl"
N_KELAS = 4


def smoke_test() -> None:
    """Uji bentuk masukan, embedding, dan keluaran pada tensor sintetis (2, 64, 101)."""
    import torch
    from model import PannsCnn6, TLClassifierHead

    torch.manual_seed(1)
    backbone = PannsCnn6.pralatih()
    head = TLClassifierHead(backbone.dim_embedding)
    x = torch.randn(2, data.N_MEL, 101)
    with torch.no_grad():
        emb = backbone(x)
        logits = head(emb)
    assert emb.shape == (2, 512), f"Bentuk embedding salah: {emb.shape}"
    assert logits.shape == (2, N_KELAS), f"Bentuk logits salah: {logits.shape}"
    print(f"Smoke test berhasil! Input: {tuple(x.shape)} -> Embedding: {tuple(emb.shape)} -> Logits: {tuple(logits.shape)}")


def hitung_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, n_kelas: int = N_KELAS) -> list[list[int]]:
    cm = np.zeros((n_kelas, n_kelas), dtype=int)
    for yt, yp in zip(y_true.astype(int), y_pred.astype(int)):
        if 0 <= yt < n_kelas and 0 <= yp < n_kelas:
            cm[yt, yp] += 1
    return cm.tolist()


def latih_dan_prediksi(
    seed: int,
    final: bool,
    hp: argparse.Namespace | None = None,
) -> tuple[np.ndarray, np.ndarray | None]:
    """Latih model Transfer Learning PANNs Cnn6 dan kembalikan (pred_val, pred_test|None)."""
    import torch
    import torch.nn.functional as F
    from model import PannsCnn6, TLClassifierHead

    if hp is None:
        hp = argparse.Namespace(
            epoch=25, batch=64, lr=1e-3, wd=1e-2, dropout=0.3,
            freeze_blocks=3, tanpa_norm_emb=False, device="auto",
        )

    torch.manual_seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    pilihan_device = getattr(hp, "device", "auto")
    device = torch.device(
        "cuda" if pilihan_device == "auto" and torch.cuda.is_available()
        else "cpu" if pilihan_device == "auto" else pilihan_device
    )
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA diminta tetapi tidak tersedia.")
    hp.perangkat = torch.cuda.get_device_name(device) if device.type == "cuda" else "cpu laptop"
    hp.device_aktual = str(device)
    Xtr, ytr, Xva, yva, Xte, _ = data.muat()

    backbone = PannsCnn6.pralatih().to(device)
    head = TLClassifierHead(backbone.dim_embedding, dropout=hp.dropout).to(device)
    y_tr = torch.as_tensor(ytr, dtype=torch.long, device=device)
    y_va_np = np.asarray(yva, dtype=np.int64)

    if hp.freeze_blocks >= 4:
        # Mode ekstraktor beku penuh (conv_block1..4 + fc1 dibekukan)
        backbone.requires_grad_(False)
        backbone.eval()

        @torch.no_grad()
        def ekstrak_penuh(fitur: np.ndarray) -> torch.Tensor:
            x = torch.as_tensor(fitur, dtype=torch.float32, device=device)
            return torch.cat([backbone(b) for b in x.split(128)], dim=0)

        E_tr = ekstrak_penuh(Xtr)
        E_va = ekstrak_penuh(Xva)
        if not hp.tanpa_norm_emb:
            emb_mean = E_tr.mean(dim=0, keepdim=True)
            emb_std = E_tr.std(dim=0, keepdim=True) + 1e-6
        else:
            emb_mean = torch.zeros((1, backbone.dim_embedding), device=device)
            emb_std = torch.ones((1, backbone.dim_embedding), device=device)

        E_tr_n = (E_tr - emb_mean) / emb_std
        E_va_n = (E_va - emb_mean) / emb_std

        opt = torch.optim.AdamW(head.parameters(), lr=hp.lr, weight_decay=hp.wd)
        terbaik_acc, terbaik_head = -1.0, None
        for ep in range(hp.epoch):
            head.train()
            total_loss = 0.0
            for idx in torch.randperm(len(E_tr_n), device=device).split(hp.batch):
                opt.zero_grad()
                loss = F.cross_entropy(head(E_tr_n[idx]), y_tr[idx])
                loss.backward()
                opt.step()
                total_loss += loss.item() * len(idx)
            head.eval()
            with torch.no_grad():
                p_val = head(E_va_n).argmax(dim=1).cpu().numpy()
            acc = float((p_val == y_va_np).mean())
            if acc > terbaik_acc:
                terbaik_acc = acc
                terbaik_head = copy.deepcopy(head.state_dict())

        head.load_state_dict(terbaik_head)
        head.eval()
        with torch.no_grad():
            pred_val = head(E_va_n).argmax(dim=1).cpu().numpy()
            pred_test = None
            if final and Xte is not None:
                E_te_n = (ekstrak_penuh(Xte) - emb_mean) / emb_std
                pred_test = head(E_te_n).argmax(dim=1).cpu().numpy()
    else:
        # Mode partial fine-tuning: bn0 + conv_block1..3 dibekukan, conv_block4 + fc1 + head dilatih
        backbone.requires_grad_(False)
        backbone.eval()

        @torch.no_grad()
        def ekstrak_stem3(fitur: np.ndarray) -> torch.Tensor:
            x = torch.as_tensor(fitur, dtype=torch.float32, device=device)
            return torch.cat([backbone.forward_stem3(b) for b in x.split(128)], dim=0)

        Z_tr = ekstrak_stem3(Xtr)
        Z_va = ekstrak_stem3(Xva)

        backbone.conv_block4.requires_grad_(True)
        backbone.fc1.requires_grad_(True)

        emb_mean = torch.zeros((1, backbone.dim_embedding), device=device)
        emb_std = torch.ones((1, backbone.dim_embedding), device=device)

        opt = torch.optim.AdamW(
            [
                {"params": backbone.conv_block4.parameters(), "lr": hp.lr},
                {"params": backbone.fc1.parameters(), "lr": hp.lr},
                {"params": head.parameters(), "lr": hp.lr},
            ],
            weight_decay=hp.wd,
        )

        def maju_atas(z3: torch.Tensor) -> torch.Tensor:
            emb = backbone.forward_top(z3)
            return head(emb)

        terbaik_acc = -1.0
        terbaik_bb, terbaik_head = None, None
        for ep in range(hp.epoch):
            backbone.conv_block4.train()
            backbone.fc1.train()
            head.train()
            total_loss = 0.0
            for idx in torch.randperm(len(Z_tr), device=device).split(hp.batch):
                opt.zero_grad()
                loss = F.cross_entropy(maju_atas(Z_tr[idx]), y_tr[idx])
                loss.backward()
                opt.step()
                total_loss += loss.item() * len(idx)

            backbone.conv_block4.eval()
            backbone.fc1.eval()
            head.eval()
            with torch.no_grad():
                p_val = torch.cat([maju_atas(b).argmax(dim=1) for b in Z_va.split(128)]).cpu().numpy()
            acc = float((p_val == y_va_np).mean())
            print(f"epoch {ep + 1:02d}/{hp.epoch}  loss {total_loss / len(Z_tr):.4f}  val_acc {acc:.4f}", flush=True)
            if acc > terbaik_acc:
                terbaik_acc = acc
                terbaik_bb = copy.deepcopy(backbone.state_dict())
                terbaik_head = copy.deepcopy(head.state_dict())

        backbone.load_state_dict(terbaik_bb)
        head.load_state_dict(terbaik_head)
        backbone.eval()
        head.eval()
        with torch.no_grad():
            pred_val = torch.cat([maju_atas(b).argmax(dim=1) for b in Z_va.split(128)]).cpu().numpy()
            pred_test = None
            if final and Xte is not None:
                Z_te = ekstrak_stem3(Xte)
                pred_test = torch.cat([maju_atas(b).argmax(dim=1) for b in Z_te.split(128)]).cpu().numpy()

    # Simpan checkpoint lokal (diabaikan oleh .gitignore *.pt) untuk ekspor ONNX
    ckpt_path = Path(__file__).resolve().parent / "tl_best.pt"
    torch.save(
        {
            "seed": seed,
            "backbone": {k: v.cpu() for k, v in backbone.state_dict().items()},
            "head": {k: v.cpu() for k, v in head.state_dict().items()},
            "emb_mean": emb_mean.cpu(),
            "emb_std": emb_std.cpu(),
            "dropout": hp.dropout,
            "freeze_blocks": hp.freeze_blocks,
            "norm_emb": hp.freeze_blocks == 4 and not hp.tanpa_norm_emb,
            "data_hash": manifest.data_hash(f"split:{split.SEED_SPLIT}".encode()),
        },
        ckpt_path,
    )
    return pred_val.astype(np.int64), (pred_test.astype(np.int64) if pred_test is not None else None)


def catat_csv_metrik(out_dir: Path, hp: argparse.Namespace, hasil_eval: dict, pred_val: np.ndarray) -> None:
    """Simpan ringkasan run ke results/122450138/tl_metrics.csv untuk audit & pelaporan."""
    _, _, _, yva, _, _ = data.muat()
    yva = np.asarray(yva, dtype=np.int64)
    val_mae = float(np.abs(yva - pred_val).mean())
    cm = hitung_confusion_matrix(yva, pred_val)

    csv_path = out_dir / "tl_metrics.csv"
    header = [
        "seed", "freeze_blocks", "epoch", "batch", "lr", "wd", "dropout",
        "norm_emb", "val_acc", "val_macro_f1", "val_mae", "durasi_detik",
        "perangkat", "data_hash", "confusion_matrix",
    ]
    baris_baru = [
        str(hp.seed), str(hp.freeze_blocks), str(hp.epoch), str(hp.batch),
        str(hp.lr), str(hp.wd), str(hp.dropout), str(hp.freeze_blocks == 4 and not hp.tanpa_norm_emb),
        str(hasil_eval["metrik"]["val_acc"]),
        str(hasil_eval["metrik"]["val_macro_f1"]),
        str(round(val_mae, 6)),
        str(hasil_eval.get("durasi_detik", 0.0)),
        str(hasil_eval.get("perangkat", hp.perangkat)),
        str(hasil_eval.get("data_hash", "")),
        json.dumps(cm),
    ]
    # Seed yang sama boleh muncul pada konfigurasi atau versi data berbeda.
    kolom_kunci = list(range(8)) + [13]

    def kunci(baris):
        return tuple(baris[i] for i in kolom_kunci)

    baris_lama = []
    if csv_path.exists():
        with csv_path.open("r", newline="", encoding="utf-8") as f:
            pembaca = csv.reader(f)
            if next(pembaca, None) != header:
                raise ValueError(f"Header CSV tidak sesuai: {csv_path}")
            for baris in pembaca:
                if len(baris) != len(header):
                    raise ValueError(f"Baris CSV tidak lengkap: {csv_path}")
                if baris[1] == "3":
                    baris[7] = "False"
                if kunci(baris) != kunci(baris_baru):
                    baris_lama.append(baris)
    baris_semua = sorted(baris_lama + [baris_baru], key=kunci)
    with tempfile.NamedTemporaryFile(
        mode="w", newline="", encoding="utf-8", dir=out_dir, delete=False,
    ) as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(baris_semua)
        sementara = f.name
    os.replace(sementara, csv_path)

    konfigurasi = dict(zip(header[:8], baris_baru[:8]))
    konfigurasi["data_hash"] = hasil_eval["data_hash"]
    kode = hashlib.sha256()
    for nama in ("run.py", "model.py"):
        kode.update(Path(__file__).with_name(nama).read_bytes())
    konfigurasi["kode_sha256"] = kode.hexdigest()
    identitas = {k: v for k, v in konfigurasi.items() if k != "seed"}
    identitas_json = json.dumps(identitas, sort_keys=True).encode()
    eksperimen = hashlib.sha256(identitas_json).hexdigest()[:12]
    arsip = out_dir / "experiments" / eksperimen / f"seed_{hp.seed}"
    arsip.mkdir(parents=True, exist_ok=True)
    np.save(arsip / "pred_val.npy", pred_val)
    shutil.copy2(out_dir / "metrics.json", arsip / "metrics.json")
    catatan = {
        "konfigurasi": konfigurasi, "device": hp.device_aktual,
        "val_mae": val_mae, "confusion_matrix": cm,
    }
    (arsip / "run.json").write_text(
        json.dumps(catatan, indent=2) + "\n", encoding="utf-8",
    )
    if hp.final:
        shutil.copy2(out_dir / "pred_test.npy", arsip / "pred_test.npy")
    print(f"Arsip eksperimen: {arsip.relative_to(AKAR)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=1, help="Seed eksperimen (wajib untuk run evaluasi)")
    ap.add_argument("--final", action="store_true", help="sprint terakhir: evaluasi data uji sekali")
    ap.add_argument("--perangkat", default="cpu laptop", help="label perangkat, diperbarui dari perangkat aktual")
    ap.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    ap.add_argument("--epoch", type=int, default=25)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--wd", type=float, default=1e-2, help="weight decay AdamW")
    ap.add_argument("--dropout", type=float, default=0.3)
    ap.add_argument("--freeze-blocks", type=int, default=3, choices=[3, 4],
                    help="3: fine-tune conv_block4+fc1+head (default); 4: bekukan seluruh backbone")
    ap.add_argument("--tanpa-norm-emb", action="store_true", help="ablation: tanpa normalisasi embedding")
    ap.add_argument("--smoke-test", action="store_true", help="uji cepat arsitektur pada tensor sintetis")
    a = ap.parse_args()

    if a.epoch < 1 or a.batch < 1 or a.lr <= 0 or a.wd < 0 or not 0 <= a.dropout < 1:
        ap.error("epoch/batch/lr harus positif, wd >= 0, dan 0 <= dropout < 1")
    if a.freeze_blocks == 3 and a.tanpa_norm_emb:
        ap.error("--tanpa-norm-emb hanya berlaku untuk --freeze-blocks 4")

    if a.smoke_test:
        smoke_test()
        return

    if os.environ.get("DATA_SINTETIS") == "1":
        ap.error("DATA_SINTETIS=1 aktif. Gunakan --smoke-test untuk uji arsitektur.")
    t0 = time.time()
    pred_val, pred_test = latih_dan_prediksi(a.seed, a.final, a)
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

    hasil_eval = json.loads((out / "metrics.json").read_text("utf-8"))
    catat_csv_metrik(out, a, hasil_eval, pred_val)


if __name__ == "__main__":
    main()
