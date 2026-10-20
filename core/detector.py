"""
File analyzer: recommends lossless or AV1 mode based on the file's properties.
"""
import os
import subprocess
import json

# Extensions that are already heavily compressed — lossless will gain ~0%.
PRECOMPRESSED_EXTS = {
    ".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v",  # video
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", # images
    ".zip", ".gz", ".7z", ".rar", ".bz2", ".xz", ".zst",  # archives
    ".pdf", ".docx", ".xlsx", ".pptx",  # office
    ".mp3", ".aac", ".m4a", ".ogg", ".opus",  # audio
}

VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}


def probe_video(path: str) -> dict | None:
    """
    Return {duration_s, codec, width, height, bitrate_kbps} or None if not a video.
    Uses ffprobe — if it's not installed, returns None.
    """
    try:
        out = subprocess.run(
            [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=codec_name,width,height,bit_rate,duration",
                "-of", "json", path,
            ],
            capture_output=True, text=True, timeout=10,
        )
        if out.returncode != 0:
            return None
        data = json.loads(out.stdout)
        streams = data.get("streams", [])
        if not streams:
            return None
        s = streams[0]
        duration = float(s.get("duration") or 0)
        if duration == 0:
            # Fallback: probe format-level duration
            out2 = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "json", path],
                capture_output=True, text=True, timeout=10,
            )
            duration = float(json.loads(out2.stdout).get("format", {}).get("duration", 0))
        return {
            "duration_s": duration,
            "codec": s.get("codec_name", "unknown"),
            "width": int(s.get("width", 0)),
            "height": int(s.get("height", 0)),
            "bitrate_kbps": int(int(s.get("bit_rate", 0)) / 1000) if s.get("bit_rate") else 0,
        }
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return None


def analyze(path: str) -> dict:
    """
    Returns a recommendation object the frontend can display to the user.
    """
    ext = os.path.splitext(path)[1].lower()
    size = os.path.getsize(path)

    # Detect video first — this is the main "help the user" case
    if ext in VIDEO_EXTS:
        info = probe_video(path)
        if info:
            codec = info["codec"].lower()
            already_modern = codec in ("av1",)
            return {
                "category": "video",
                "recommended_mode": "transcode",
                "reason": (
                    f"{codec.upper()} {info['width']}×{info['height']}, "
                    f"{info['duration_s']:.0f}s. "
                    + ("AV1 re-encode can save 40–60%." if not already_modern
                       else "Already AV1 — lossless mode is the only option.")
                ),
                "lossless_expected_pct": 1.0,
                "transcode_expected_pct": 45.0 if not already_modern else 0.0,
                "duration_s": info["duration_s"],
                "codec": codec,
            }
        return {
            "category": "video",
            "recommended_mode": "transcode",
            "reason": "Video detected. AV1 re-encode typically saves 40–60%.",
            "lossless_expected_pct": 1.0,
            "transcode_expected_pct": 45.0,
            "duration_s": None,
            "codec": None,
        }

    # Pre-compressed non-video — be honest that lossless won't help
    if ext in PRECOMPRESSED_EXTS:
        return {
            "category": "precompressed",
            "recommended_mode": "lossless",
            "reason": (
                f"{ext} is already compressed. Lossless will save ~0%. "
                "Use this if you need exact restoration, not size reduction."
            ),
            "lossless_expected_pct": 2.0,
            "transcode_expected_pct": None,
        }

    # Text-like — lossless is a huge win
    return {
        "category": "text",
        "recommended_mode": "lossless",
        "reason": f"{ext or 'file'} is text-like. Lossless typically saves 80–99%.",
        "lossless_expected_pct": 85.0,
        "transcode_expected_pct": None,
    }