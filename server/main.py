from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os, uuid, tempfile, json
import shutil

load_dotenv()

from core.compressor import compress_file
from core.restorer import restore_file
from core.transcode import transcode_av1, ACTIVE_PROCESSES
from core.detector import analyze
from core.transcriber import generate_subtitles
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
    work = tempfile.mkdtemp()
    safe_name = os.path.basename(file.filename or "upload.bin")
    src_path = os.path.join(work, safe_name)
    with open(src_path, "wb") as f:
        while chunk := await file.read(1 << 20):
            f.write(chunk)
    try:
        return analyze(src_path)
    finally:
        try: os.unlink(src_path)
        except OSError: pass


# ---------- Compress ----------
@app.post("/api/v1/compress")
async def compress(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    mode: str = Form("lossless"),
) -> dict:
    if mode not in ("lossless", "transcode"):
        raise HTTPException(400, "mode must be 'lossless' or 'transcode'")

    if mode == "transcode" and not _ffmpeg_available():
        raise HTTPException(status_code=503, detail="AV1 transcoding requires FFmpeg.")

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
                id=archive_id, filename=file.filename or safe_name,
                size_orig=result["orig_size"], size_comp=result["compressed_size"],
                sha256_orig=result["orig_sha256"], storage_path=arc_path, mode="lossless",
            ))
            db.commit()
        finally:
            db.close()

        _update_job(
            job_id, status="completed", progress=100.0,
            result_json=json.dumps({
                "archive_id": archive_id, "mode": "lossless",
                "orig_size": result["orig_size"], "compressed_size": result["compressed_size"],
                "savings_pct": 100 * (1 - result["compressed_size"] / result["orig_size"]),
                "sha256": result["orig_sha256"], "download_url": f"/api/v1/archives/{archive_id}/download",
            }),
        )
        return {"job_id": job_id, "mode": "lossless", "status": "completed"}

    out_path = os.path.join(STORAGE, f"{archive_id}.mp4")
    background_tasks.add_task(_run_transcode, job_id, archive_id, src_path, out_path, file.filename or safe_name)
    return {"job_id": job_id, "mode": "transcode", "status": "queued"}


def _run_transcode(job_id: str, archive_id: str, src_path: str, out_path: str, original_name: str) -> None:
    _update_job(job_id, status="processing", progress=1.0)
    def on_progress(pct: float) -> None: _update_job(job_id, progress=pct)

    try:
        result = transcode_av1(src_path, out_path, job_id=job_id, crf=32, preset=8, on_progress=on_progress)
    except Exception as e:
        _update_job(job_id, status="failed", message=str(e))
        try: os.unlink(src_path)
        except OSError: pass
        return

    db = SessionLocal()
    try:
        db.add(Archive(
            id=archive_id, filename=original_name, size_orig=result["orig_size"],
            size_comp=result["new_size"], sha256_orig="", storage_path=out_path, mode="transcode",
        ))
        db.commit()
    finally:
        db.close()

    _update_job(
        job_id, status="completed", progress=100.0,
        result_json=json.dumps({
            "archive_id": archive_id, "mode": "transcode",
            "orig_size": result["orig_size"], "compressed_size": result["new_size"],
            "savings_pct": result["savings_pct"], "codec": "av1", "crf": result["crf"],
            "download_url": f"/api/v1/archives/{archive_id}/download",
            "warning": "AV1 output is not bit-identical to the original.",
        }),
    )
    try: os.unlink(src_path)
    except OSError: pass


def _update_job(job_id: str, **fields) -> None:
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job:
            for k, v in fields.items(): setattr(job, k, v)
            db.commit()
    finally:
        db.close()


# ---------- Jobs ----------
@app.get("/api/v1/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if not job: raise HTTPException(404, "Job not found")
        return {
            "job_id": job.id, "kind": job.kind, "status": job.status,
            "progress": job.progress, "message": job.message,
            "result": json.loads(job.result_json) if job.result_json else None,
        }
    finally:
        db.close()

@app.post("/api/v1/jobs/{job_id}/cancel")
def cancel_job(job_id: str) -> dict:
    if job_id in ACTIVE_PROCESSES:
        ACTIVE_PROCESSES[job_id].terminate()
    _update_job(job_id, status="failed", message="Cancelled by user")
    return {"ok": True, "message": "Job cancelled"}


# ---------- Archives & Preview ----------
@app.get("/api/v1/archives/{archive_id}/download")
def download(archive_id: str):
    db = SessionLocal()
    try:
        row = db.get(Archive, archive_id)
        if not row: raise HTTPException(404, "Not found")
        ext = "mp4" if row.mode == "transcode" else "akp"
        mime = "video/mp4" if row.mode == "transcode" else "application/octet-stream"
        return FileResponse(row.storage_path, filename=f"{row.filename}.{ext}", media_type=mime)
    finally:
        db.close()

@app.post("/api/v1/restore")
async def restore(file: UploadFile = File(...)):
    work = tempfile.mkdtemp()
    arc_path = os.path.join(work, "input.akp")
    with open(arc_path, "wb") as f:
        while chunk := await file.read(1 << 20): f.write(chunk)
    out_path = os.path.join(work, "restored.bin")
    try:
        restore_file(arc_path, out_path)
    except Exception as e:
        raise HTTPException(400, str(e))
    return FileResponse(out_path, filename="restored.bin")

@app.post("/api/v1/preview")
async def preview_akp(file: UploadFile = File(...)):
    work = tempfile.mkdtemp()
    arc_path = os.path.join(work, "input.akp")
    with open(arc_path, "wb") as f:
        while chunk := await file.read(4 << 20): f.write(chunk) # 4MB chunks
    
    preview_id = uuid.uuid4().hex
    out_path = os.path.join(STORAGE, f"preview_{preview_id}.mp4")
    
    try:
        # verify=False makes the preview load instantly!
        restore_file(arc_path, out_path, verify=False)
        return {"preview_url": f"/api/v1/preview/{preview_id}"}
    except Exception as e:
        raise HTTPException(400, f"Failed to restore video: {str(e)}")
    finally:
        try: os.unlink(arc_path)
        except OSError: pass

@app.get("/api/v1/preview/{preview_id}")
def serve_preview(preview_id: str):
    out_path = os.path.join(STORAGE, f"preview_{preview_id}.mp4")
    if not os.path.exists(out_path): raise HTTPException(404, "Preview not found")
    return FileResponse(out_path, media_type="video/mp4", headers={"Accept-Ranges": "bytes"})

@app.post("/api/v1/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form("auto")
):
    work = tempfile.mkdtemp()
    audio_path = os.path.join(work, "audio.wav")
    vtt_path = os.path.join(work, "subtitle.vtt")
    
    with open(audio_path, "wb") as f:
        while chunk := await file.read(1 << 20):
            f.write(chunk)
            
    try:
        method = generate_subtitles(audio_path, vtt_path, language)
        return {
            "status": "success",
            "method": method,
            "vtt_content": open(vtt_path, "r", encoding="utf-8").read()
        }
    except Exception as e:
        raise HTTPException(500, f"Transcription failed: {str(e)}")
    finally:
        try: os.remove(audio_path); os.remove(vtt_path)
        except: pass
        
@app.get("/api/v1/preview/{preview_id}/subtitle")
def serve_subtitle(preview_id: str):
    vtt_path = os.path.join(STORAGE, f"preview_{preview_id}.vtt")
    if not os.path.exists(vtt_path): raise HTTPException(404, "Subtitle not found")
    return FileResponse(vtt_path, media_type="text/vtt")