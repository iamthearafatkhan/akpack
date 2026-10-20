from core.format import (
    CODEC_RAW, CODEC_ZSTD, CODEC_BROTLI, CODEC_DEFLATE, CODEC_XZ,
)
from .raw import RawCodec
from .zstd import ZstdCodec
from .brotli import BrotliCodec
from .deflate import DeflateCodec
from .xz import XZCodec

REGISTRY = {
    CODEC_RAW:     RawCodec(),
    CODEC_ZSTD:    ZstdCodec(),
    CODEC_BROTLI:  BrotliCodec(),
    CODEC_DEFLATE: DeflateCodec(),
    CODEC_XZ:      XZCodec(),
}

def get_codec(codec_id: int):
    if codec_id not in REGISTRY:
        raise ValueError(f"Unknown codec id {codec_id}")
    return REGISTRY[codec_id]