import zstandard as zstd
from .base import Codec
from core.format import CODEC_ZSTD

class ZstdCodec(Codec):
    id = CODEC_ZSTD
    name = "zstd"

    def __init__(self, level: int = 10):
        self._c = zstd.ZstdCompressor(level=level)
        self._d = zstd.ZstdDecompressor()

    def compress(self, data: bytes) -> bytes:
        return self._c.compress(data)

    def decompress(self, data: bytes, expected_len: int) -> bytes:
        return self._d.decompress(data, max_output_size=expected_len)