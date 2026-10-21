# 🌿 AKPack

**Honest file compression.** Lossless for exact byte restoration, or AV1 transcoding for 50% smaller video.

AKPack is a universal file compression and delivery platform. It features a custom `.akp` archive format, a blazing-fast Python CLI, and a beautiful web interface for compressing, restoring, and streaming media.

## 🚀 Features

* **Lossless Compression:** Compress text, code, datasets, and logs by 80–99% with zero data loss. Restores to the exact original bytes (SHA-256 verified).
* **AV1 Video Transcoding:** Re-encode H.264/H.265 videos to AV1, reducing file size by 40–60% with visually identical quality.
* **Watch Instantly:** Upload an `.akp` file and stream the video directly in the browser without downloading the original file.
* **AI Subtitles (Coming Soon):** Generate free, accurate subtitles using Whisper AI.
* **Open Source CLI:** Run heavy video transcoding locally on your laptop, for free.

## 🛠 Tech Stack

* **Backend:** Python 3.12, FastAPI, SQLAlchemy, PostgreSQL (Neon), Zstandard, Brotli, FFmpeg (SVT-AV1).
* **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Framer Motion.
* **Deployment:** Cloudflare Pages (Frontend), Render (Backend), Neon (Database).

## 💻 Local Development Setup

### 1. Requirements
* Python 3.11+
* Node.js 18+
* FFmpeg (with `libsvtav1` support) for AV1 transcoding.

### 2. Backend Setup
```bash
# Clone the repository
git clone https://github.com/iamthearafatkhan/akpack.git
cd akpack

# Install Python dependencies
pip install -e ".[dev,server]"

# Setup environment variables
cp .env.example .env
# Edit .env and add your Neon PostgreSQL URL

# Run the backend
./run.sh
```
### 3. Frontend Setup
```bash
cd web
npm install
npm run dev
```
The app will be available at http://localhost:5173.

## 📦 CLI Usage
The AKPack CLI allows you to compress and restore files without the web interface.

```bash
# Compress a file losslessly
akp compress dataset.csv dataset.akp

# Verify an archive
akp verify dataset.akp

# Restore an archive
akp restore dataset.akp dataset_restored.csv

# Transcode a video to AV1 (requires FFmpeg)
akp compress movie.mp4 movie.av1.mp4 --mode transcode
```
## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
