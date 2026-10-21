import os
import logging
import requests
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

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
    
    if language and language != "auto":
        kwargs["language"] = language
        
    res = client.audio.transcriptions.create(**kwargs)
    return res

def transcribe_huggingface(audio_path: str) -> str:
    """Tier 2: Hugging Face API (Free Backup)."""
    if not HF_TOKEN:
        raise ValueError("HF_TOKEN is missing.")
    
    API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    with open(audio_path, "rb") as f:
        data = f.read()
    
    response = requests.post(API_URL, headers=headers, data=data, timeout=60)
    if response.status_code != 200:
        raise Exception(f"HF API Error: {response.text}")
    
    result = response.json()
    if isinstance(result, list) and len(result) > 0:
        chunks = result[0].get("chunks", [])
        vtt = "WEBVTT\n\n"
        for i, c in enumerate(chunks):
            start, end = c["timestamp"]
            start_str = f"{int(start // 60):02d}:{start % 60:06.3f}"
            end_str = f"{int(end // 60):02d}:{end % 60:06.3f}" if end else "00:00:10.000"
            vtt += f"{i+1}\n{start_str} --> {end_str}\n{c['text'].strip()}\n\n"
        return vtt
    raise Exception("Could not parse HF response.")

def generate_subtitles(audio_path: str, output_vtt: str, language: str = "auto") -> str:
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    method_used = "Unknown"

    if file_size_mb > 24:
        raise Exception("Audio chunk too large. Please split into smaller files.")

    try:
        logger.info("Attempting Groq API...")
        vtt = transcribe_groq(audio_path, language)
        method_used = "Groq API (Fast)"
    except Exception as e:
        logger.warning(f"Groq failed: {e}. Trying Hugging Face...")
        try:
            vtt = transcribe_huggingface(audio_path)
            method_used = "Hugging Face API"
        except Exception as e2:
            logger.error(f"HF failed: {e2}.")
            raise Exception("Both Groq and Hugging Face failed. Please check your API keys on Render.")

    with open(output_vtt, "w", encoding="utf-8") as f:
        f.write(vtt)
    
    return method_used