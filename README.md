<div align="center">

# 🌿 AKPack

### Honest Compression. Exact Restoration. Lightning-Fast Delivery.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)](https://fastapi.tiangolo.com/)

</div>

---


## 🧩 The Problem

Sending large files (videos, datasets, backups) is painful. You either lose quality with lossy compression, or you deal with massive file sizes and slow uploads.

**AKPack** solves this with two modes:
1.  **Lossless (`.akp`):** Shrinks text, code, and logs by 80–99% while guaranteeing **bit-for-bit exact restoration**. No quality loss, ever.
2.  **AV1 Transcode:** Shrinks video files by 40–60% with visually near-identical quality for modern browsers.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Zero-Quality-Loss** | Lossless mode uses Zstandard and Brotli to restore files exactly. |
| **AV1 Video Compression** | Re-encodes H.264/H.265 videos to AV1, saving up to 60% size. |
| **Browser Playback** | Watch restored `.akp` videos instantly without downloading. |
| **AI Subtitles** | Free, automatic transcription using Groq Whisper or local CPU fallback. |
| **Native Desktop App** | Standalone `.exe` tool for Windows to compress/transcode offline. |

---

## 🚀 Quick Start (Local)

### 1. Backend
```bash
# Install Python dependencies
pip install -e ".[server,dev]"

# Install optional AV1 & Subtitle dependencies
pip install faster-whisper av<19 groq huggingface_hub

# Start the API server
uvicorn server.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd web
npm install
npm run dev
```
The app will be available at http://localhost:5173.

## 🛠 Tech Stack

Frontend: React, TypeScript, Vite, Tailwind CSS, Framer Motion

Backend: FastAPI, Python 3.11+, SQLAlchemy

Engine: Zstandard, Brotli, FFmpeg (SVT-AV1)

AI: Groq API / Hugging Face / faster-whisper

Database: SQLite (Local) / Neon PostgreSQL (Cloud)

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
