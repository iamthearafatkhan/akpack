from typing import Iterator

def iter_chunks(path: str, chunk_size: int) -> Iterator[tuple[int, bytes]]:
    """Yield (offset, chunk_bytes). Last chunk may be shorter."""
    offset = 0
    with open(path, "rb") as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            yield offset, data
            offset += len(data)