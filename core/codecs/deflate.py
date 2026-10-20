import zlib
from .base import Codec
from core.format import CODEC_DEFLATE

class DeflateCodec(Codec):
    id = CODEC_DEFLATE
    name = "deflate"

    def compress(self, data: bytes) -> bytes:
        return zlib.compress(data, level=9)

    def decompress(self, data: bytes, expected_len: int) -> bytes:
        return zlib.decompress(data)