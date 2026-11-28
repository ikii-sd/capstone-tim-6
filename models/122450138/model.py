"""Ekstraktor PANNs Cnn6 pralatih dan classifier untuk empat kelas Tim 6."""
from __future__ import annotations

from pathlib import Path

import torch
from torch import nn

# Checkpoint AudioSet resmi dari penulis PANNs.
CHECKPOINT = "Cnn6_mAP=0.343.pth"
URL = f"https://zenodo.org/records/3987831/files/{CHECKPOINT}?download=1"


class BlokKonvolusi(nn.Module):
    def __init__(self, kanal_masuk: int, kanal_keluar: int):
        super().__init__()
        self.conv1 = nn.Conv2d(kanal_masuk, kanal_keluar, 5, padding=2, bias=False)
        self.bn1 = nn.BatchNorm2d(kanal_keluar)
        self.pool = nn.AvgPool2d(2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.pool(self.bn1(self.conv1(x)).relu())


class PannsCnn6(nn.Module):
    """Bagian ekstraksi Cnn6, diadaptasi dari implementasi MIT penulis PANNs.

    https://github.com/qiuqiangkong/audioset_tagging_cnn/blob/master/pytorch/models.py
    """
    dim_embedding = 512

    def __init__(self):
        super().__init__()
        # Log-mel tim sudah dinormalisasi per pita. Pakai skala dan bias
        # terlatih dari bn0 dengan statistik normalisasi milik tim.
        self.bn0 = nn.BatchNorm2d(64)
        self.conv_block1 = BlokKonvolusi(1, 64)
        self.conv_block2 = BlokKonvolusi(64, 128)
        self.conv_block3 = BlokKonvolusi(128, 256)
        self.conv_block4 = BlokKonvolusi(256, 512)
        self.fc1 = nn.Linear(512, self.dim_embedding)

    @classmethod
    def pralatih(cls) -> "PannsCnn6":
        folder = Path(torch.hub.get_dir()) / "checkpoints"
        try:
            checkpoint = torch.hub.load_state_dict_from_url(
                URL, model_dir=str(folder), file_name=CHECKPOINT,
                map_location="cpu", weights_only=True,
            )
        except OSError as exc:
            raise RuntimeError(f"Unduh bobot PANNs dari {URL} ke {folder / CHECKPOINT}") from exc
        model = cls()
        bobot = checkpoint["model"]
        # Pilih seluruh parameter ekstraktor. Frontend waveform dan classifier
        # AudioSet dikeluarkan karena masukan serta labelnya berbeda.
        model.load_state_dict({k: bobot[k] for k in model.state_dict()})
        return model.requires_grad_(False).eval()

    def forward_stem3(self, logmel: torch.Tensor) -> torch.Tensor:
        """Ekstraksi fitur bertingkat hingga conv_block3: (N, 64, T) -> (N, 256, T//8, 8)."""
        if not torch.jit.is_tracing():
            if logmel.ndim != 3 or logmel.shape[1] != 64 or logmel.shape[2] < 16:
                raise ValueError("Masukan PANNs harus berbentuk (N, 64, T) dengan T >= 16.")
        x = logmel * self.bn0.weight[None, :, None] + self.bn0.bias[None, :, None]
        x = x.transpose(1, 2).unsqueeze(1)  # (N, 1, waktu, mel)
        x = self.conv_block1(x)
        x = self.conv_block2(x)
        return self.conv_block3(x)

    def forward_top(self, z3: torch.Tensor) -> torch.Tensor:
        """Bagian atas Cnn6 (conv_block4 + global temporal pooling + fc1): (N, 256, T', 8) -> (N, 512)."""
        x = self.conv_block4(z3).mean(dim=3)
        return self.fc1(x.amax(dim=2) + x.mean(dim=2)).relu()

    def forward(self, logmel: torch.Tensor) -> torch.Tensor:
        return self.forward_top(self.forward_stem3(logmel))


class TLClassifierHead(nn.Module):
    def __init__(self, embedding_dim: int = 512, dropout: float = 0.3):
        super().__init__()
        self.classifier = nn.Sequential(
            nn.Linear(embedding_dim, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, 4),
        )

    def forward(self, embedding: torch.Tensor) -> torch.Tensor:
        return self.classifier(embedding)


class PannsCnn6EndToEnd(nn.Module):
    """Bungkus PannsCnn6 + normalisasi embedding latih + TLClassifierHead untuk inferensi/ONNX."""

    def __init__(self, backbone: PannsCnn6, head: TLClassifierHead,
                 emb_mean: torch.Tensor | None = None, emb_std: torch.Tensor | None = None):
        super().__init__()
        self.backbone = backbone
        self.head = head
        if emb_mean is None:
            emb_mean = torch.zeros(1, backbone.dim_embedding)
        if emb_std is None:
            emb_std = torch.ones(1, backbone.dim_embedding)
        self.register_buffer("emb_mean", emb_mean.reshape(1, -1).float())
        self.register_buffer("emb_std", emb_std.reshape(1, -1).float())

    def forward(self, logmel: torch.Tensor) -> torch.Tensor:
        emb = self.backbone(logmel)
        emb = (emb - self.emb_mean) / self.emb_std
        return self.head(emb)
