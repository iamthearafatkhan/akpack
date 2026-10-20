# AKPack benchmark results

Platform: Windows / Python 3.13.5
Codecs: zstd-10, brotli-9, deflate-9 (adaptive per chunk)

| File | Category | Original | Compressed | Savings | Time | Verified |
|---|---|---:|---:|---:|---:|---:|
| `big.log` | log | 6,090,000 B | 4,691 B | 99.9% | 0.14s | ✅ |
| `big.json` | json | 1,047,780 B | 28,788 B | 97.3% | 0.12s | ✅ |
| `big.csv` | csv | 2,162,222 B | 222,902 B | 89.7% | 0.88s | ✅ |
| `sample.py` | source | 227,780 B | 7,410 B | 96.7% | 0.04s | ✅ |
| `sample.sql` | sql | 2,306,670 B | 58,848 B | 97.4% | 0.25s | ✅ |
| `sample.xml` | xml | 566,204 B | 29,033 B | 94.9% | 0.12s | ✅ |
| `sample.html` | html | 1,348,916 B | 18,203 B | 98.7% | 0.11s | ✅ |
| `random.bin` | random | 2,097,152 B | 2,097,618 B | -0.0% | 0.19s | ✅ |
| `pseudo_png.bin` | incompressible | 2,097,160 B | 2,097,785 B | -0.0% | 0.20s | ✅ |
