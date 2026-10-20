import hashlib

def sha256_bytes(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()

def sha256_file(path: str, chunk_size: int = 1 << 20) -> bytes:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.digest()

def sha256_hex(b: bytes) -> str:
    return b.hex()