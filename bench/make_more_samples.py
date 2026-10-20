"""Generate samples across categories so we can measure reality."""
import os
import random

OUT = os.path.dirname(os.path.abspath(__file__))

def write(name, data):
    path = os.path.join(OUT, name)
    with open(path, "wb") as f:
        f.write(data if isinstance(data, bytes) else data.encode())
    print(f"{name:25s}  {os.path.getsize(path):>12,} bytes")

# ---- Compressible category ----
write("sample.py", "".join(
    f"def func_{i}(x, y):\n    return x * y + {i}\n\n" for i in range(5000)
))
write("sample.sql", "".join(
    f"INSERT INTO users (id, name, email) VALUES ({i}, 'u{i}', 'u{i}@x.com');\n"
    for i in range(30000)
))
write("sample.xml", "<root>" + "".join(
    f"<item id='{i}'><name>n{i}</name><val>{i*7}</val></item>" for i in range(10000)
) + "</root>")

# ---- Marginal category ----
write("sample.html", "<html><body>" + "".join(
    f"<p>Paragraph {i}: the quick brown fox jumps over the lazy dog.</p>"
    for i in range(20000)
) + "</body></html>")

# ---- Incompressible category ----
write("random.bin", os.urandom(2 * 1024 * 1024))       # pure random → 0%
write("pseudo_png.bin", b"\x89PNG\r\n\x1a\n" + os.urandom(2 * 1024 * 1024))