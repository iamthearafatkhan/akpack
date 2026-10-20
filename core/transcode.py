"""
AV1 transcoding via SVT-AV1 with live progress.
"""
import subprocess
import os
from typing import Callable

ACTIVE_PROCESSES: dict[str, subprocess.Popen] = {}

def transcode_av1(
    src_path: str,
    out_path: str,
    *,
    job_id: str,
    crf: int = 32,
    preset: int = 8,
    on_progress: Callable[[float], None] | None = None,
) -> dict:
    orig_size = os.path.getsize(src_path)

    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", src_path],
            capture_output=True, text=True, timeout=10,
        )
        duration_s = float(probe.stdout.strip() or 0)
    except (FileNotFoundError, ValueError, Exception):
        duration_s = 0

    cmd = [
        "ffmpeg", "-y",
        "-i", src_path,
        "-c:v", "libsvtav1",
        "-crf", str(crf),
        "-preset", str(preset),
        "-c:a", "copy",
        "-movflags", "+faststart",
        "-progress", "pipe:1",
        "-nostats",
        out_path,
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    
    ACTIVE_PROCESSES[job_id] = proc

    try:
        for line in proc.stdout:
            line = line.strip()
            if on_progress and duration_s > 0 and line.startswith("out_time_us="):
                try:
                    us = int(line.split("=", 1)[1])
                    pct = min(99.0, 100.0 * (us / 1_000_000) / duration_s)
                    on_progress(pct)
                except ValueError:
                    pass
            elif line == "progress=end":
                if on_progress:
                    on_progress(100.0)

        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError("FFmpeg failed or was cancelled")
    finally:
        # THIS BLOCK MUST BE INDENTED UNDER THE TRY
        ACTIVE_PROCESSES.pop(job_id, None)

    new_size = os.path.getsize(out_path)
    return {
        "orig_size": orig_size,
        "new_size": new_size,
        "savings_pct": 100 * (1 - new_size / orig_size) if orig_size else 0,
        "codec": "av1",
        "crf": crf,
        "lossless": False,
    }