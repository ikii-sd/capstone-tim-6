
import torch

from transformer import TransformerKlasifikasi


def test_transformer_forward():
    model = TransformerKlasifikasi()
    x = torch.randn(2, 64, 101)

    model.eval()
    with torch.no_grad():
        output = model(x)

    assert output.shape == (2, 4)
    assert torch.isfinite(output).all()
