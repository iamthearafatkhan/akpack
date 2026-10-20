"""High-level: restore an .akp archive to exact original bytes."""
import os
from core.container import read_header
from core.codecs import get_codec
from core.integrity import sha256_file, sha256_bytes
from core.format import AKPFormatError

def restore_file(archive_path: str, out_path: str) -> dict:
    with open(archive_path, "rb") as f:
        header = read_header(f)
        chunks = header["manifest"]["chunks"]

        # payload starts right after header+manifest
        # (read_header consumed them)

        with open(out_path, "wb") as out:
            for meta in chunks:
                payload = f.read(meta["stored_len"])
                if len(payload) != meta["stored_len"]:
                    raise AKPFormatError(f"Truncated chunk {meta['idx']}")

                codec = get_codec(meta["codec"])
                chunk = codec.decompress(payload, meta["orig_len"])

                if len(chunk) != meta["orig_len"]:
                    raise AKPFormatError(
                        f"Chunk {meta['idx']} length mismatch: "
                        f"{len(chunk)} != {meta['orig_len']}"
                    )
                if sha256_bytes(chunk).hex() != meta["sha256"]:
                    raise AKPFormatError(f"Chunk {meta['idx']} hash mismatch")

                out.write(chunk)

    actual = sha256_file(out_path)
    if actual != header["orig_sha256"]:
        raise AKPFormatError("Whole-file hash mismatch — restoration corrupted")

    return {
        "restored_size": os.path.getsize(out_path),
        "orig_sha256": header["orig_sha256"].hex(),
        "verified": True,
    }