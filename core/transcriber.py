import os
import logging
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def transcribe_groq(audio_path: str, language: str) -> str:
    """Tier 1: Groq API (Fastest, Free)."""
    if not GROQ_API_KEY: 
        raise ValueError("GROQ_API_KEY is missing.")
    
    client = Groq(api_key=GROQ_API_KEY)
    
    kwargs = {
        "file": (os.path.basename(audio_path), open(audio_path, "rb").read()),
        "model": "whisper-large-v3-turbo",
        "response_format": "vtt",
    }
    
    # If language is not "auto", force Whisper to use that language
    if language and language != "auto":
        kwargs["language"] = language
        
    res = client.audio.transcriptions.create(**kwargs)
    return res

def transcribe_local(audio_path: str, language: str) -> str:
    """Tier 2: Local CPU Fallback (No internet required)."""
    from faster_whisper import WhisperModel
    
    logger.warning("Using local faster-whisper CPU. This may take a while...")
    model = WhisperModel("base", device="cpu", compute_type="int8")
    
    lang = None if language == "auto" else language
    segments, _ = model.transcribe(audio_path, beam_size=5, language=lang)
    
    vtt = "WEBVTT\n\n"
    for i, seg in enumerate(segments):
        start_str = f"{int(seg.start // 60):02d}:{seg.start % 60:06.3f}"
        end_str = f"{int(seg.end // 60):02d}:{seg.end % 60:06.3f}"
        vtt += f"{i+1}\n{start_str} --> {end_str}\n{seg.text.strip()}\n\n"
        
    return vtt

def generate_subtitles(audio_path: str, output_vtt: str, language: str = "auto") -> str:
    """
    Orchestrates transcription. 
    Note: The browser now sends a tiny .wav file directly, so we don't need FFmpeg here anymore.
    """
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    method_used = "Unknown"

    # Groq has a 25MB limit. Since browser extracts 16kHz mono WAV, most audio will be under this.
    if file_size_mb <= 24:
        try:
            vtt = transcribe_groq(audio_path, language)
            method_used = "Groq API (Fast)"
        except Exception as e:
            logger.warning(f"Groq failed: {e}. Falling back to local CPU.")
            vtt = transcribe_local(audio_path, language)
            method_used = "Local CPU (Slow)"
    else:
        vtt = transcribe_local(audio_path, language)
        method_used = "Local CPU (Large File)"

    with open(output_vtt, "w", encoding="utf-8") as f:
        f.write(vtt)
    
    return method_used