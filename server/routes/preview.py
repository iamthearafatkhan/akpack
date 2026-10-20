# server/routes/preview.py
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse
from core.container import read_header
from core.codecs import get_codec
import os

router = APIRouter()

@router.get("/api/v1/preview/{archive_id}")
async def preview_video(archive_id: str, range: str | None = Header(None)):
    """Stream video bytes from an .akp archive using HTTP Range requests."""
    # 1. Find the archive file
    archive_path = os.path.join(STORAGE, f"{archive_id}.akp")
    if not os.path.exists(archive_path):
        raise HTTPException(404, "Archive not found")
    
    # 2. Read manifest to find byte ranges
    with open(archive_path, "rb") as f:
        header = read_header(f)
    
    orig_size = header["orig_size"]
    
    # 3. Parse Range header (e.g. "bytes=0-1048575")
    start, end = 0, orig_size - 1
    if range and range.startswith("bytes="):
        parts = range.replace("bytes=", "").split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if len(parts) > 1 and parts[1] else orig_size - 1
    
    # 4. Find which chunks cover [start, end], decompress only those
    async def stream_chunks():
        with open(archive_path, "rb") as f:
            read_header(f)  # skip to payload
            for meta in header["manifest"]["chunks"]:
                chunk_start = meta["orig_off"]
                chunk_end = chunk_start + meta["orig_len"] - 1
                # Skip chunks outside requested range
                if chunk_end < start or chunk_start > end:
                    f.seek(meta["stored_len"], 1)
                    continue
                payload = f.read(meta["stored_len"])
                chunk = get_codec(meta["codec"]).decompress(payload, meta["orig_len"])
                # Trim to requested range
                lo = max(0, start - chunk_start)
                hi = min(len(chunk), end - chunk_start + 1)
                yield chunk[lo:hi]
    
    return StreamingResponse(
        stream_chunks(),
        media_type="video/mp4",
        headers={
            "Content-Range": f"bytes {start}-{end}/{orig_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(end - start + 1),
        },
        status_code=206  # Partial Content
    )