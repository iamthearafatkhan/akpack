from .base import Codec
from core.format import CODEC_RAW

class RawCodec(Codec):
    id = CODEC_RAW
    name = "raw"

    def compress(self, data: bytes) -> bytes:
        return data

    def decompress(self, data: bytes, expected_len: int) -> bytes:
        return data