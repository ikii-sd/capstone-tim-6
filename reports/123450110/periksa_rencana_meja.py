from pathlib import Path
from itertools import product
import yaml

ROOT = Path(__file__).resolve().parents[2]
path = ROOT / "rencana" / "t06-hitung-alat-suara.yaml"

with path.open(encoding="utf-8") as f:
    rencana = yaml.safe_load(f)

faktor = rencana["faktor"]
nama_faktor = ["kipas", "pompa", "buzzer", "lampu"]

kombinasi = list(product(*(faktor[n] for n in nama_faktor)))
ulangan = int(rencana["ulangan"])
durasi = int(rencana["durasi_kondisi_detik"])
jeda = int(rencana["jeda_detik"])

total = len(kombinasi) * ulangan
estimasi_detik = total * (durasi + jeda)

assert rencana["tim"] == 6
assert len(kombinasi) == 24
assert ulangan == 12
assert total == 288
assert durasi == 20
assert jeda == 2
assert rencana["rekam"]["audio"]["sample_rate"] == 16000

print("=== PEMERIKSAAN RENCANA MEJA TIM 6 ===")
print(f"File rencana       : {path.relative_to(ROOT)}")
print(f"Jumlah kombinasi   : {len(kombinasi)}")
print(f"Jumlah ulangan     : {ulangan}")
print(f"Total kondisi      : {total}")
print(f"Durasi per kondisi : {durasi} detik")
print(f"Jeda               : {jeda} detik")
print(f"Estimasi waktu     : {estimasi_detik} detik")
print(f"                     = {estimasi_detik / 60:.2f} menit")
print("Status pemeriksaan : PASS")
print("Catatan: Ini validasi konfigurasi, bukan eksekusi meja.py.")