
import torch
from transformer import TransformerKlasifikasi

# Simulasi satu batch log-mel
X = torch.randn(16, 64, 101)
y = torch.randint(0, 4, (16,))

model = TransformerKlasifikasi()
output = model(X)

loss = torch.nn.functional.cross_entropy(output, y)

print("Input       :", X.shape)
print("Output      :", output.shape)
print("Loss        :", loss.item())
print(
    "Parameter   :",
    sum(p.numel() for p in model.parameters())
)

assert output.shape == (16, 4)
print("TRANSFORMER BERHASIL DIUJI")
