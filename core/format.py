"""AKP v1 format constants and helpers."""
import struct

MAGIC = b"AKP1"
VERSION = 1
HEADER_STRUCT = struct.Struct("<4sHHIIQQ32s")
HEADER_SIZE = HEADER_STRUCT.size          # 64 bytes
DEFAULT_CHUNK_SIZE = 1 * 1024 * 1024      # 1 MiB

# codec registry ids (stable forever)
CODEC_RAW = 0
CODEC_ZSTD = 1
CODEC_BROTLI = 2
CODEC_DEFLATE = 3
CODEC_XZ = 4

CODEC_NAME = {
    CODEC_RAW: "raw",
    CODEC_ZSTD: "zstd",
    CODEC_BROTLI: "brotli",
    CODEC_DEFLATE: "deflate",
    CODEC_XZ: "xz",
}

class AKPFormatError(Exception):
    pass