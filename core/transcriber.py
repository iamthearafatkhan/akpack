import os
import subprocess
import math
import logging
from pathlib import Path
from groq import Groq
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "whisper-large-v3-turbo"
MAX_GROQ_MB = 24  # Groq limit is 25MB

def extract_audio(video_path: str, output_path: str, start_time: float = 0, duration: float = None):
    """Extracts audio to 16kHz mono WAV using FFmpeg."""
    cmd = ["ffmpeg", "-y", "-i", video_path]
    if start_time > 0:
        cmd.extend(["-ss", str(start_time)])
    if duration:
        cmd.extend(["-t", str(duration)])
    cmd.extend(["-vn", "-ac", "1", "-ar", "16000", "-acodec", "pcm_s16le", output_path])
    subprocess.run(cmd, check=True, capture_output=True)

def transcribe_with_groq(audio_path: str) -> str:
    """Primary method: Groq Whisper API."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is missing.")
    
    client = Groq(api_key=GROQ_API_KEY)
    with open(audio_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            file=(Path(audio_path).name, f.read()),
            model=GROQ_MODEL,
            response_format="vtt", # Returns WebVTT directly
        )
    return transcription

def transcribe_fallback(audio_path: str) -> str:
    """Fallback method: Local faster-whisper (CPU)."""
    logger.warning("Falling back to local faster-whisper...")
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio_path, beam_size=5)
    
    vtt = "WEBVTT\n\n"
    for i, seg in enumerate(segments):
        start = f"{int(seg.start // 3600):02d}:{int((seg.start % 3600) // 60):02d}:{seg.start % 60:06.3f}"
        end = f"{int(seg.end // 3600):02d}:{int((seg.end % 3600) // 60):02d}:{seg.end % 60:06.3f}"
        vtt += f"{i+1}\n{start} --> {end}\n{seg.text.strip()}\n\n"
    return vtt

def generate_subtitles(video_path: str, output_vtt: str):
    """Handles chunking for >24MB files and orchestrates fallback."""
    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    
    if file_size_mb <= MAX_GROQ_MB:
        try:
            vtt_content = transcribe_with_groq(video_path)
            with open(output_vtt, "w", encoding="utf-8") as f:
                f.write(vtt_content)
            return "Groq API (Fast)"
        except Exception as e:
            logger.error(f"Groq failed: {e}. Falling back.")
            
    # Fallback if file too large or Groq fails
    vtt_content = transcribe_fallback(video_path)
    with open(output_vtt, "w", encoding="utf-8") as f:
        f.write(vtt_content)
    return "Local Fallback (CPU)"