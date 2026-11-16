"""Ekspor model Transfer Learning PANNs Cnn6 (122450138) ke ONNX dan verifikasi kompatibilitas output.

Penggunaan:
    python models/122450138/export_onnx.py [--checkpoint models/122450138/tl_best.pt]
                                           [--out results/122450138/tl_panns_cnn6.onnx]
                                           [--out-head results/122450138/tl_head.onnx]
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
import torch
from torch import nn

AKAR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AKAR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.protokol import data  # noqa: E402
from model import PannsCnn6, PannsCnn6EndToEnd, TLClassifierHead  # noqa: E402


class NormHeadONNX(nn.Module):
    """Classifier head beserta normalisasi embedding latih untuk inferensi ringan."""

    def __init__(self, head: TLClassifierHead, emb_mean: torch.Tensor, emb_std: torch.Tensor):
        super().__init__()
        self.head = head
        self.register_buffer("emb_mean", emb_mean.reshape(1, -1).float())
        self.register_buffer("emb_std", emb_std.reshape(1, -1).float())

    def forward(self, embedding: torch.Tensor) -> torch.Tensor:
        return self.head((embedding - self.emb_mean) / self.emb_std)


def muat_komponen(ckpt_path: Path) -> tuple[PannsCnn6EndToEnd, NormHeadONNX]:
    backbone = PannsCnn6.pralatih()
    if ckpt_path.exists():
        ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=True)
        backbone.load_state_dict(ckpt["backbone"])
        head = TLClassifierHead(backbone.dim_embedding, dropout=float(ckpt.get("dropout", 0.3)))
        head.load_state_dict(ckpt["head"])
        emb_mean = ckpt.get("emb_mean", torch.zeros(1, backbone.dim_embedding))
        emb_std = ckpt.get("emb_std", torch.ones(1, backbone.dim_embedding))
    else:
        head = TLClassifierHead(backbone.dim_embedding)
        emb_mean = torch.zeros(1, backbone.dim_embedding)
        emb_std = torch.ones(1, backbone.dim_embedding)
    e2e = PannsCnn6EndToEnd(backbone, head, emb_mean=emb_mean, emb_std=emb_std).eval()
    norm_head = NormHeadONNX(head, emb_mean=emb_mean, emb_std=emb_std).eval()
    return e2e, norm_head


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--checkpoint", default=str(Path(__file__).resolve().parent / "tl_best.pt"),
                    help="Jalur checkpoint PyTorch hasil pelatihan run.py")
    ap.add_argument("--out", default=str(AKAR / "results" / "122450138" / "tl_panns_cnn6.onnx"),
                    help="Jalur berkas keluaran ONNX end-to-end (log-mel -> logits 4 kelas)")
    ap.add_argument("--out-head", default=str(AKAR / "results" / "122450138" / "tl_head.onnx"),
                    help="Jalur berkas keluaran ONNX khusus classifier head (embedding -> logits 4 kelas)")
    ap.add_argument("--opset", type=int, default=17, help="Versi ONNX opset")
    a = ap.parse_args()

    ckpt_path = Path(a.checkpoint)
    out_path = Path(a.out)
    out_head_path = Path(a.out_head)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_head_path.parent.mkdir(parents=True, exist_ok=True)

    model_e2e, model_head = muat_komponen(ckpt_path)
    contoh_logmel = torch.randn(2, data.N_MEL, 101, dtype=torch.float32)
    contoh_emb = torch.randn(2, PannsCnn6.dim_embedding, dtype=torch.float32)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        torch.onnx.export(
            model_e2e,
            contoh_logmel,
            str(out_path),
            export_params=True,
            opset_version=a.opset,
            do_constant_folding=True,
            input_names=["logmel"],
            output_names=["logits"],
            dynamic_axes={"logmel": {0: "batch_size"}, "logits": {0: "batch_size"}},
            dynamo=False,
        )
        torch.onnx.export(
            model_head,
            contoh_emb,
            str(out_head_path),
            export_params=True,
            opset_version=a.opset,
            do_constant_folding=True,
            input_names=["embedding"],
            output_names=["logits"],
            dynamic_axes={"embedding": {0: "batch_size"}, "logits": {0: "batch_size"}},
            dynamo=False,
        )

    onnx.checker.check_model(onnx.load(str(out_path)))
    onnx.checker.check_model(onnx.load(str(out_head_path)))

    ukuran_e2e_mb = out_path.stat().st_size / (1024 * 1024)
    ukuran_head_kb = out_head_path.stat().st_size / 1024

    sess_e2e = ort.InferenceSession(str(out_path), providers=["CPUExecutionProvider"])
    sess_head = ort.InferenceSession(str(out_head_path), providers=["CPUExecutionProvider"])

    with torch.no_grad():
        pt_out = model_e2e(contoh_logmel).numpy()
        pt_head_out = model_head(contoh_emb).numpy()
    ort_out = sess_e2e.run(["logits"], {"logmel": contoh_logmel.numpy()})[0]
    ort_head_out = sess_head.run(["logits"], {"embedding": contoh_emb.numpy()})[0]

    selisih_e2e = float(np.max(np.abs(pt_out - ort_out)))
    selisih_head = float(np.max(np.abs(pt_head_out - ort_head_out)))
    assert np.allclose(pt_out, ort_out, atol=1e-4), f"Selisih E2E terlalu besar: {selisih_e2e}"
    assert np.allclose(pt_head_out, ort_head_out, atol=1e-5), f"Selisih Head terlalu besar: {selisih_head}"

    print(f"Ekspor ONNX End-to-End : {out_path} ({ukuran_e2e_mb:.2f} MiB) | maks |PT - ORT| = {selisih_e2e:.2e}")
    print(f"Ekspor ONNX Head-Only  : {out_head_path} ({ukuran_head_kb:.2f} KiB) | maks |PT - ORT| = {selisih_head:.2e}")

    try:
        _, _, Xva, yva, _, _ = data.muat()
        Xva_f32 = np.asarray(Xva, dtype=np.float32)
        with torch.no_grad():
            pt_logits = torch.cat([model_e2e(torch.from_numpy(b)) for b in np.array_split(Xva_f32, 4)], dim=0).numpy()
        ort_logits = np.concatenate([sess_e2e.run(["logits"], {"logmel": b})[0] for b in np.array_split(Xva_f32, 4)], axis=0)
        diff_val = float(np.max(np.abs(pt_logits - ort_logits)))
        pt_pred = pt_logits.argmax(axis=1)
        ort_pred = ort_logits.argmax(axis=1)
        kecocokan_pred = float((pt_pred == ort_pred).mean())
        acc_ort = float((ort_pred == yva).mean())
        assert kecocokan_pred == 1.0, f"Prediksi kelas berbeda antara PyTorch dan ONNX: {kecocokan_pred}"
        print(f"Verifikasi data validasi ({len(yva)} jendela): kecocokan prediksi = {kecocokan_pred*100:.2f}%, "
              f"val_acc ORT = {acc_ort:.4f}, maks |PyTorch - ORT| = {diff_val:.2e}")
    except FileNotFoundError:
        print("Catatan: folder sesi asli tidak ditemukan, verifikasi cukup pada data sintetis.")


if __name__ == "__main__":
    main()
