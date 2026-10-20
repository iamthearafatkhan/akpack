"""High-level: compress a file into an .akp archive."""
import json
import os
import tempfile
from core.format import DEFAULT_CHUNK_SIZE
from core.chunker import iter_chunks
from core.integrity import sha256_file
from core.router import choose_and_compress
from core.container import write_header


def compress_file(
    src_path: str,
    out_path: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    candidates: list[int] | None = None,
) -> dict:
    """
    Compress src_path into an AKP v1 archive at out_path.

    Two-pass design:
      Pass 1 — compress each chunk to a temp file, collect metadata.
      Pass 2 — write header + manifest + payload to the final file.

    This avoids the "reserve header size" problem entirely: we only write
    the final file once we know the exact manifest size.
    """
    orig_size = os.path.getsize(src_path)
    orig_hash = sha256_file(src_path)

    if candidates is None:
        candidates = [1, 2, 3]  # zstd, brotli, deflate

    chunks_meta: list[dict] = []
    fd, tmp_payload_path = tempfile.mkstemp(suffix=".akp_payload")

    try:
        # Pass 1 — compress chunks to temp file
        with os.fdopen(fd, "wb") as tmp:
            for idx, (offset, chunk) in enumerate(iter_chunks(src_path, chunk_size)):
                cid, payload, chunk_hash = choose_and_compress(chunk, candidates=candidates)
                chunks_meta.append({
                    "idx": idx,
                    "orig_off": offset,
                    "orig_len": len(chunk),
                    "stored_len": len(payload),
                    "codec": cid,
                    "sha256": chunk_hash.hex(),
                })
                tmp.write(payload)

        manifest = json.dumps({
            "filename": os.path.basename(src_path),
            "mime": "application/octet-stream",
            "chunks": chunks_meta,
        }).encode("utf-8")

        # Pass 2 — write final archive in one pass
        with open(out_path, "wb") as out:
            write_header(
                out,
                chunk_size=chunk_size,
                chunk_count=len(chunks_meta),
                orig_size=orig_size,
                manifest=manifest,
                orig_sha256=orig_hash,
            )
            with open(tmp_payload_path, "rb") as tmp_read:
                while buf := tmp_read.read(1 << 20):
                    out.write(buf)

        return {
            "orig_size": orig_size,
            "compressed_size": os.path.getsize(out_path),
            "orig_sha256": orig_hash.hex(),
            "chunks": len(chunks_meta),
        }

    finally:
        try:
            os.unlink(tmp_payload_path)
        except OSError:
            pass