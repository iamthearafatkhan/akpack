import os, tempfile, pytest
from core.compressor import compress_file
from core.restorer import restore_file
from core.integrity import sha256_file

@pytest.mark.parametrize("size", [0, 1, 1024, 1024*1024 + 1, 5*1024*1024])
def test_roundtrip(size):
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in.bin")
        arc = os.path.join(td, "in.akp")
        out = os.path.join(td, "out.bin")
        with open(src, "wb") as f:
            f.write(os.urandom(size))
        compress_file(src, arc)
        restore_file(arc, out)
        assert sha256_file(src) == sha256_file(out)
        assert os.path.getsize(src) == os.path.getsize(out)

def test_corruption_detected():
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in.bin")
        arc = os.path.join(td, "in.akp")
        out = os.path.join(td, "out.bin")
        with open(src, "wb") as f:
            f.write(b"hello world" * 1000)
        compress_file(src, arc)
        # flip one byte in the payload
        with open(arc, "r+b") as f:
            f.seek(-1, 2)
            f.write(b"\x00")
        with pytest.raises(Exception):
            restore_file(arc, out)