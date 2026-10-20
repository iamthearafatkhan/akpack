"""Generate sample files that actually compress well."""
import json
import os
import random

OUT = os.path.dirname(os.path.abspath(__file__))

# JSON: 20k records → compresses 80–90% with zstd
data = [{"id": i, "name": f"user_{i}", "active": i % 2 == 0} for i in range(20000)]
with open(os.path.join(OUT, "big.json"), "w", encoding="utf-8") as f:
    json.dump(data, f)

# CSV: 50k rows → compresses well
with open(os.path.join(OUT, "big.csv"), "w", encoding="utf-8") as f:
    f.write("id,name,email,score\n")
    for i in range(50000):
        f.write(f"{i},user_{i},user_{i}@example.com,{random.randint(0, 100)}\n")

# Repeated log → compresses extremely well
with open(os.path.join(OUT, "big.log"), "w", encoding="utf-8") as f:
    for i in range(100000):
        f.write(f"2026-10-20T12:00:{i % 60:02d} INFO service=api user=user_{i % 100} status=ok\n")

for name in ("big.json", "big.csv", "big.log"):
    path = os.path.join(OUT, name)
    print(f"{name:12s}  {os.path.getsize(path):>12,} bytes")