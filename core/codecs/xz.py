import lzma
from .base import Codec
from core.format import CODEC_XZ

class XZCodec(Codec):
    id = CODEC_XZ
    name = "xz"

    def compress(self, data: bytes) -> bytes:
        return lzma.compress(data, preset=6)

    def decompress(self, data: bytes, expected_len: int) -> bytes:
        return lzma.decompress(data)