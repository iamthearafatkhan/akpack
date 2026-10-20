"""
Cross-category benchmark. No shell, no pipes, no encoding issues.
Writes a markdown report to docs/benchmarks.md.
"""
import os
import time
from core.compressor import compress_file
from core.restorer import restore_file
from core.integrity import sha256_file

BENCH_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BENCH_DIR)
DOCS = os.path.join(REPO_ROOT, "docs")
os.makedirs(DOCS, exist_ok=True)

SAMPLES = [
    ("big.log",        "log"),
    ("big.json",       "json"),
    ("big.csv",        "csv"),
    ("sample.py",      "source"),
    ("sample.sql",     "sql"),
    ("sample.xml",     "xml"),
    ("sample.html",    "html"),
    ("random.bin",     "random"),
    ("pseudo_png.bin", "incompressible"),
]


def bench_one(name: str) -> dict | None:
    src = os.path.join(BENCH_DIR, name)
    if not os.path.exists(src):
        return None
    arc = src + ".akp"
    out = src + ".out"

    t0 = time.time()
    r = compress_file(src, arc)
    t_comp = time.time() - t0

    restore_file(arc, out)
    verified = sha256_file(src) == sha256_file(out)
    os.unlink(out)

    orig = r["orig_size"]
    comp = r["compressed_size"]
    savings = 100 * (1 - comp / orig) if orig else 0.0

    return {
        "name": name,
        "orig": orig,
        "comp": comp,
        "savings": savings,
        "time_s": t_comp,
        "verified": verified,
    }


def main() -> None:
    rows: list[dict] = []
    for name, _category in SAMPLES:
        row = bench_one(name)
        if row is not None:
            rows.append(row)

    header = f"{'file':18s} {'original':>12s} {'compressed':>12s} {'savings':>9s} {'time':>8s} {'ok':>4s}"
    print(header)
    print("-" * len(header))
    for r in rows:
        print(
            f"{r['name']:18s} "
            f"{r['orig']:>12,} "
            f"{r['comp']:>12,} "
            f"{r['savings']:>8.1f}% "
            f"{r['time_s']:>7.2f}s "
            f"{str(r['verified']):>4s}"
        )

    md_lines = [
        "# AKPack benchmark results",
        "",
        f"Platform: Windows / Python {os.sys.version.split()[0]}",
        f"Codecs: zstd-10, brotli-9, deflate-9 (adaptive per chunk)",
        "",
        "| File | Category | Original | Compressed | Savings | Time | Verified |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for (name, category), r in zip(SAMPLES, rows):
        md_lines.append(
            f"| `{name}` | {category} | {r['orig']:,} B | {r['comp']:,} B "
            f"| {r['savings']:.1f}% | {r['time_s']:.2f}s | {'✅' if r['verified'] else '❌'} |"
        )

    out_md = os.path.join(DOCS, "benchmarks.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    print()
    print(f"Report written to {out_md}")


if __name__ == "__main__":
    main()