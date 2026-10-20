from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os, uuid, tempfile, json

load_dotenv()

from core.compressor import compress_file
from core.restorer import restore_file
from core.transcode import transcode_av1
from core.detector import analyze
from .db import Base, engine, SessionLocal
from .models import Archive, Job

Base.metadata.create_all(engine)

app = FastAPI(title="AKPack API")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

STORAGE = os.getenv("AKP_STORAGE", "./storage")
os.makedirs(STORAGE, exist_ok=True)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "ffmpeg": _ffmpeg_available()}


@app.get("/")
def root() -> dict:
    return {"service": "AKPack API", "docs": "/docs", "health": "/health"}


def _ffmpeg_available() -> bool:
    import subprocess
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=3)
        return True
    except (FileNotFoundError, Exception):
        return False


# ---------- Analyze ----------
@app.post("/api/v1/analyze")
async def analyze_endpoint(file: UploadFile = File(...)) -> dict:
    """Upload a file, get a mode recommendation + expected savings."""
    work = tempfile.mkdtemp()
    safe_name = os.path.basename(file.filename or "upload.bin")
    src_path = os.path.join(work, safe_name)
    with open(src_path, "wb") as f:
        while chunk := await file.read(1 << 20):
            f.write(chunk)
    try:
        return analyze(src_path)
    finally:
        try:
            os.unlink(src_path)
        except OSError:
            pass


# ---------- Compress (two modes) ----------
@app.post("/api/v1/compress")
async def compress(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    mode: str = Form("lossless"),
) -> dict:
    if mode not in ("lossless", "transcode"):
        raise HTTPException(400, "mode must be 'lossless' or 'transcode'")

    # >>> THIS is the missing block <<<
    # Refuse AV1 cleanly if this server has no FFmpeg (e.g. Render free tier).
    if mode == "transcode" and not _ffmpeg_available():
        raise HTTPException(
            status_code=503,
            detail=(
                "AV1 transcoding requires FFmpeg with libsvtav1, which is not "
                "installed on this server. Install FFmpeg locally and use the "
                "AKPack CLI, or contact us for Pro access."
            ),
        )

    archive_id = uuid.uuid4().hex
    job_id = uuid.uuid4().hex
    work = tempfile.mkdtemp()
    safe_name = os.path.basename(file.filename or "upload.bin")
    src_path = os.path.join(work, safe_name)

    with open(src_path, "wb") as f:
        while chunk := await file.read(1 << 20):
            f.write(chunk)

    db = SessionLocal()
    try:
        db.add(Job(id=job_id, kind=mode, archive_id=archive_id, status="queued"))
        db.commit()
    finally:
        db.close()

    if mode == "lossless":
        arc_path = os.path.join(STORAGE, f"{archive_id}.akp")
        try:
            result = compress_file(src_path, arc_path)
        except Exception as e:
            _update_job(job_id, status="failed", message=str(e))
            raise HTTPException(500, str(e))

        db = SessionLocal()
        try:
            db.add(Archive(
                id=archive_id,
                filename=file.filename or safe_name,
                size_orig=result["orig_size"],
                size_comp=result["compressed_size"],
                sha256_orig=result["orig_sha256"],
                storage_path=arc_path,
                mode="lossless",
            ))
            db.commit()
        finally:
            db.close()

        _update_job(
            job_id, status="completed", progress=100.0,
            result_json=json.dumps({
                "archive_id": archive_id,
                "mode": "lossless",
                "orig_size": result["orig_size"],
                "compressed_size": result["compressed_size"],
                "savings_pct": 100 * (1 - result["compressed_size"] / result["orig_size"]),
                "sha256": result["orig_sha256"],
                "download_url": f"/api/v1/archives/{archive_id}/download",
            }),
        )
        return {"job_id": job_id, "mode": "lossless", "status": "completed"}

    # AV1: run in background
    out_path = os.path.join(STORAGE, f"{archive_id}.mp4")
    background_tasks.add_task(
        _run_transcode, job_id, archive_id, src_path, out_path, file.filename or safe_name
    )
    return {"job_id": job_id, "mode": "transcode", "status": "queued"}


def _run_transcode(job_id: str, archive_id: str, src_path: str, out_path: str, original_name: str) -> None:
    """Background worker: transcode to AV1, track progress, update DB."""
    _update_job(job_id, status="processing", progress=1.0)

    def on_progress(pct: float) -> None:
        _update_job(job_id, progress=pct)

    try:
        result = transcode_av1(src_path, out_path, job_id=job_id, crf=32, preset=8, on_progress=on_progress)
    except Exception as e:
        _update_job(job_id, status="failed", message=str(e))
        try:
            os.unlink(src_path)
        except OSError:
            pass
        return

    db = SessionLocal()
    try:
        db.add(Archive(
            id=archive_id,
            filename=original_name,
            size_orig=result["orig_size"],
            size_comp=result["new_size"],
            sha256_orig="",
            storage_path=out_path,
            mode="transcode",
        ))
        db.commit()
    finally:
        db.close()

    _update_job(
        job_id, status="completed", progress=100.0,
        result_json=json.dumps({
            "archive_id": archive_id,
            "mode": "transcode",
            "orig_size": result["orig_size"],
            "compressed_size": result["new_size"],
            "savings_pct": result["savings_pct"],
            "codec": "av1",
            "crf": result["crf"],
            "download_url": f"/api/v1/archives/{archive_id}/download",
            "warning": "AV1 output is not bit-identical to the original. It is visually near-transparent.",
        }),
    )
    try:
        os.unlink(src_path)
    except OSError:
        pass


def _update_job(job_id: str, **fields) -> None:
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job:
            for k, v in fields.items():
                setattr(job, k, v)
            db.commit()
    finally:
        db.close()


# ---------- Job status ----------
@app.get("/api/v1/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if not job:
            raise HTTPException(404, "Job not found")
        return {
            "job_id": job.id,
            "kind": job.kind,
            "status": job.status,
            "progress": job.progress,
            "message": job.message,
            "result": json.loads(job.result_json) if job.result_json else None,
        }
    finally:
        db.close()


# ---------- Archive endpoints ----------
@app.get("/api/v1/archives/{archive_id}")
def get_archive(archive_id: str) -> dict:
    db = SessionLocal()
    try:
        row = db.get(Archive, archive_id)
        if not row:
            raise HTTPException(404, "Not found")
        return {
            "id": row.id, "filename": row.filename, "mode": row.mode,
            "orig_size": row.size_orig, "compressed_size": row.size_comp,
            "sha256": row.sha256_orig,
        }
    finally:
        db.close()


@app.get("/api/v1/archives/{archive_id}/download")
def download(archive_id: str):
    db = SessionLocal()
    try:
        row = db.get(Archive, archive_id)
        if not row:
            raise HTTPException(404, "Not found")
        ext = "mp4" if row.mode == "transcode" else "akp"
        mime = "video/mp4" if row.mode == "transcode" else "application/octet-stream"
        return FileResponse(
            row.storage_path, 
            filename=f"{row.filename}.{ext}",
            media_type=mime
        )
    finally:
        db.close()


@app.post("/api/v1/restore")
async def restore(file: UploadFile = File(...)):
    work = tempfile.mkdtemp()
    arc_path = os.path.join(work, "input.akp")
    with open(arc_path, "wb") as f:
        while chunk := await file.read(1 << 20):
            f.write(chunk)
    out_path = os.path.join(work, "restored.bin")
    try:
        restore_file(arc_path, out_path)
    except Exception as e:
        raise HTTPException(400, str(e))
    return FileResponse(out_path, filename="restored.bin")

@app.post("/api/v1/jobs/{job_id}/cancel")
def cancel_job(job_id: str) -> dict:
    from core.transcode import ACTIVE_PROCESSES
    if job_id in ACTIVE_PROCESSES:
        ACTIVE_PROCESSES[job_id].terminate() # Kills FFmpeg
        _update_job(job_id, status="failed", message="Cancelled by user")
        return {"ok": True, "message": "Job cancelled"}
    
    # If it's a lossless job or already finished
    _update_job(job_id, status="failed", message="Cancelled by user")
    return {"ok": True, "message": "Job marked as cancelled"}


@app.post("/api/v1/preview")
async def preview_akp(file: UploadFile = File(...)):
    """Restores an .akp file on the server and returns a URL to stream the video."""
    work = tempfile.mkdtemp()
    arc_path = os.path.join(work, "input.akp")
    with open(arc_path, "wb") as f:
        while chunk := await file.read(1 << 20):
            f.write(chunk)
    
    preview_id = uuid.uuid4().hex
    out_path = os.path.join(STORAGE, f"preview_{preview_id}.mp4")
    
    try:
        # Restore to an mp4 file in storage
        restore_file(arc_path, out_path)
        return {"preview_url": f"/api/v1/preview/{preview_id}"}
    except Exception as e:
        raise HTTPException(400, f"Failed to restore video: {str(e)}")
    finally:
        try: os.unlink(arc_path)
        except OSError: pass

@app.get("/api/v1/preview/{preview_id}")
def serve_preview(preview_id: str):
    """Serves the restored video for the <video> tag."""
    out_path = os.path.join(STORAGE, f"preview_{preview_id}.mp4")
    if not os.path.exists(out_path):
        raise HTTPException(404, "Preview not found")
    return FileResponse(out_path, media_type="video/mp4")
