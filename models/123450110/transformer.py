
import torch
import torch.nn as nn


class TransformerKlasifikasi(nn.Module):
    def __init__(
        self,
        n_mel=64,
        d_model=64,
        nhead=4,
        num_layers=2,
        num_classes=4,
        max_seq_len=101,
        dropout=0.1,
    ):
        super().__init__()

        self.input_projection = nn.Linear(n_mel, d_model)

        self.positional_embedding = nn.Parameter(
            torch.zeros(1, max_seq_len, d_model)
        )
        nn.init.normal_(self.positional_embedding, mean=0.0, std=0.02)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            batch_first=True,
            activation="gelu",
        )

        self.encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers,
        )

        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(d_model, num_classes)

    def forward(self, x):
        if x.ndim != 3:
            raise ValueError("Input harus berbentuk [B, 64, 101]")

        x = x.transpose(1, 2)

        x = self.input_projection(x)
        x = x + self.positional_embedding[:, :x.shape[1], :]

        x = self.encoder(x)
        x = x.mean(dim=1)

        x = self.dropout(x)
        return self.classifier(x)
