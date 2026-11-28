# Hasil komparasi (dibangkitkan run_all.py)

| NIM | Model | seed | val_acc | val_macro_f1 | test_acc | durasi (s) | perangkat |
|---|---|---|---|---|---|---|---|
| baseline | mfcc_mean_std_random_forest | 2026 | 0.9120 | 0.8959 | — | 64 | cpu laptop |
| 122450048 | cnn | 1 | 0.9977 | 0.9976 | nan | 322 | cpu laptop |
| 122450138 | tl | 1 | 0.9560 | 0.9569 | nan | 1717 | cpu laptop |
| 123450077 | ae | 1 | 0.7361 | 0.7731 | nan | 192 | cpu laptop |
| 123450110 | trf | 1 | 0.9491 | 0.9323 | nan | 109 | cpu laptop |
