<div align="center">

# 🌿 AKPack

### Honest Compression. Exact Restoration. Studio-Grade Playback.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](#license)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)](https://fastapi.tiangolo.com/)

</div>

---

## 🧩 The Problem

Sending large files (videos, datasets, backups) is painful. You either lose quality with lossy compression, or you deal with massive file sizes and slow uploads. Furthermore, watching compressed media often requires sketchy third-party players filled with ads.

**AKPack** solves this with a complete ecosystem: a custom archive format, a lightning-fast web platform, and a desktop media studio.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Zero-Quality-Loss** | Lossless `.akp` format uses Zstandard and Brotli to shrink files (80–99% on text) and restores them exactly, bit-for-bit. |
| **AV1 Transcoding** | Re-encodes H.264/H.265 videos to AV1, saving up to 60% in size with near-identical visual quality. |
| **Browser Playback** | Watch restored `.akp` videos instantly on the web using WebAssembly (WASM). No server uploads required for playback. |
| **AKPack Studio** | A standalone desktop media player with native subtitle support, 4K hardware acceleration, and built-in compression tools. |
| **Manual Subtitles** | Upload `.srt` or `.vtt` files on the web, or automatically read multiple embedded subtitle tracks in the Desktop App. |

---

## 🚀 Download & Quick Start

### 1. Download AKPack Studio (Windows)
Skip the browser and get the ultimate offline experience:
* **[Download AKPack-Studio.exe](https://github.com/iamthearafatkhan/akpack/releases/latest/download/AKPack-Studio.exe)**
* Watch `.akp` files, MP4s, MKVs, and WEBMs.
* Supports multiple embedded subtitle tracks.
* Includes Lossless and AV1 compression tools.
* 200% volume boost and hardware acceleration for 4K.

### 2. Run Locally (Web)

**Backend:**
```bash
pip install -e ".[server,dev]"
uvicorn server.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd web
npm install
npm run dev
```
The app will be available at http://localhost:5173.

## ☁️ Deployment Architecture
AKPack is designed to be deployed on a zero-cost stack:

Frontend: Cloudflare Pages (React + Vite)

Backend API: Render (FastAPI)

Database: Neon PostgreSQL

Media Playback: Client-side (WASM) & VLC (Desktop)

Heavy Processing (AV1): Local Desktop App (FFmpeg)
---

## 🛠 Tech Stack

Frontend: React, TypeScript, Vite, Tailwind CSS, Framer Motion

Backend: FastAPI, Python 3.11+, SQLAlchemy

Engine: Zstandard, Brotli, FFmpeg (SVT-AV1)

AI: Groq API / Hugging Face / faster-whisper

Database: SQLite (Local) / Neon PostgreSQL (Cloud)

---

## ⚖️ Legal & Privacy
AKPack is a neutral, client-side tool.

**No File Storage:** We do not host, store, or distribute files. The web "Watch" feature decodes entirely in your browser. Your videos never touch our servers.

**Acceptable Use:** You may not use AKPack to distribute copyrighted material without authorization. See our Terms of Service.

## 📄 License
This project is licensed under the MIT License.

<details> <summary><b>Click to view the full MIT License text</b></summary>
