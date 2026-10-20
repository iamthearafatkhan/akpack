"""Adaptive chunk router: try a bounded set of codecs, keep the smallest."""
from core.codecs import get_codec
from core.format import CODEC_RAW, CODEC_ZSTD, CODEC_BROTLI, CODEC_DEFLATE
from core.integrity import sha256_bytes

# Default candidate portfolio. Start small; add XZ only if benchmarks justify.
DEFAULT_CANDIDATES = [CODEC_ZSTD, CODEC_BROTLI, CODEC_DEFLATE]

def choose_and_compress(
    chunk: bytes,
    candidates: list[int] = DEFAULT_CANDIDATES,
    min_gain_bytes: int = 64,
) -> tuple[int, bytes, bytes]:
    """
    Returns (codec_id, compressed_payload, sha256_of_original_chunk).
    Picks the smallest output that beats raw by at least min_gain_bytes;
    otherwise stores raw.
    """
    best_id = CODEC_RAW
    best_payload = chunk
    best_len = len(chunk)

    for cid in candidates:
        try:
            payload = get_codec(cid).compress(chunk)
        except Exception:
            continue
        if len(payload) < best_len - min_gain_bytes:
            best_id, best_payload, best_len = cid, payload, len(payload)

    return best_id, best_payload, sha256_bytes(chunk)