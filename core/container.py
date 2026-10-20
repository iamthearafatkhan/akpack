"""AKP v1 reader/writer."""
import json
from typing import BinaryIO
from core.format import (
    MAGIC, VERSION, HEADER_STRUCT, HEADER_SIZE, AKPFormatError,
)

def write_header(
    f: BinaryIO,
    *,
    chunk_size: int,
    chunk_count: int,
    orig_size: int,
    manifest: bytes,
    orig_sha256: bytes,
) -> None:
    if len(orig_sha256) != 32:
        raise AKPFormatError("orig_sha256 must be 32 bytes")
    f.write(HEADER_STRUCT.pack(
        MAGIC, VERSION, 0, chunk_size, chunk_count,
        orig_size, len(manifest), orig_sha256,
    ))
    f.write(manifest)

def read_header(f: BinaryIO) -> dict:
    raw = f.read(HEADER_SIZE)
    if len(raw) != HEADER_SIZE:
        raise AKPFormatError("Truncated header")
    magic, version, flags, chunk_size, chunk_count, \
        orig_size, manifest_len, orig_sha256 = HEADER_STRUCT.unpack(raw)

    if magic != MAGIC:
        raise AKPFormatError(f"Bad magic: {magic!r}")
    if version != VERSION:
        raise AKPFormatError(f"Unsupported version {version}")

    manifest_bytes = f.read(manifest_len)
    if len(manifest_bytes) != manifest_len:
        raise AKPFormatError("Truncated manifest")

    return {
        "version": version,
        "flags": flags,
        "chunk_size": chunk_size,
        "chunk_count": chunk_count,
        "orig_size": orig_size,
        "orig_sha256": orig_sha256,
        "manifest": json.loads(manifest_bytes.decode("utf-8")),
    }