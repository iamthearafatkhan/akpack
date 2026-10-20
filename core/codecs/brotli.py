import brotli
from .base import Codec
from core.format import CODEC_BROTLI

class BrotliCodec(Codec):
    id = CODEC_BROTLI
    name = "brotli"

    def __init__(self, quality: int = 9):
        self._q = quality

    def compress(self, data: bytes) -> bytes:
        return brotli.compress(data, quality=self._q)

    def decompress(self, data: bytes, expected_len: int) -> bytes:
        return brotli.decompress(data)