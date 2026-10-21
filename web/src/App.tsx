import { useEffect, useState } from "react";
import { Routes, Route } from "react-router-dom";
import { motion } from "framer-motion";
import { API } from "./lib/api";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import FAQ from "./pages/FAQ";
import Privacy from "./pages/Privacy";
import Terms from './pages/Terms';
import Loader from "./components/Loader";
import { decodeAkpInBrowser } from "./lib/akpBrowserDecoder";
import { convertSrtToVtt } from "./lib/subtitleConverter";

type Analysis = { category: string; recommended_mode: "lossless" | "transcode"; reason: string; lossless_expected_pct: number; transcode_expected_pct: number | null; duration_s?: number | null; codec?: string | null; };
type JobResult = { archive_id: string; mode: "lossless" | "transcode"; orig_size: number; compressed_size: number; savings_pct: number; download_url: string; warning?: string; };

function formatBytes(n: number): string {
    if (n < 1024) return `${n} B`;
    if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
    if (n < 1024 * 1024 * 1024) return `${(n / (1024 * 1024)).toFixed(1)} MB`;
    return `${(n / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}
function suggestedFilename(original: string, mode: "lossless" | "transcode"): string {
    if (mode === "transcode") return `${original.replace(/\.[^.]+$/, "")}.av1.mp4`;
    return `${original}.akp`;
}
async function saveToDevice(url: string, filename: string, onProgress?: (loaded: number, total: number) => void): Promise<boolean> {
    if ("showSaveFilePicker" in window) {
        try {
            const handle = await (window as any).showSaveFilePicker({ suggestedName: filename });
            const writable = await handle.createWritable();
            const resp = await fetch(url);
            if (!resp.ok) throw new Error(`Download failed`);
            const total = parseInt(resp.headers.get("content-length") || "0", 10);
            let loaded = 0; const reader = resp.body?.getReader();
            if (!reader) throw new Error("No body");
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                await writable.write(value); loaded += value.length;
                onProgress?.(loaded, total);
            }
            await writable.close(); return true;
        } catch (e: any) { if (e.name === "AbortError") return false; }
    }
    const a = document.createElement("a"); a.href = url; a.download = filename;
    document.body.appendChild(a); a.click(); document.body.removeChild(a); return true;
}

function Home() {
    const [activeTab, setActiveTab] = useState<"compress" | "restore" | "watch">("compress");

    // Compress state
    const [file, setFile] = useState<File | null>(null);
    const [analysis, setAnalysis] = useState<Analysis | null>(null);
    const [analyzing, setAnalyzing] = useState(false);
    const [mode, setMode] = useState<"lossless" | "transcode">("lossless");
    const [busy, setBusy] = useState(false);
    const [progress, setProgress] = useState(0);
    const [result, setResult] = useState<JobResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [ffmpegAvailable, setFfmpegAvailable] = useState<boolean | null>(null);
    const [autoDownload, setAutoDownload] = useState(true);
    const [downloaded, setDownloaded] = useState(false);
    const [downloading, setDownloading] = useState(false);
    const [downloadPct, setDownloadPct] = useState(0);

    // Restore state
    const [restoreFile, setRestoreFile] = useState<File | null>(null);
    const [restoring, setRestoring] = useState(false);
    const [restoreError, setRestoreError] = useState<string | null>(null);

    // Watch state
    const [watchFile, setWatchFile] = useState<File | null>(null);
    const [watching, setWatching] = useState(false);
    const [watchProgress, setWatchProgress] = useState(0);
    const [videoUrl, setVideoUrl] = useState<string | null>(null);
    const [watchError, setWatchError] = useState<string | null>(null);
    const [subtitleUrl, setSubtitleUrl] = useState<string | null>(null);

    useEffect(() => {
        fetch(`${API}/health`).then(r => r.json()).then(h => setFfmpegAvailable(h.ffmpeg === true)).catch(() => setFfmpegAvailable(false));
    }, []);

    async function onSelectFile(f: File | null) {
        setFile(f); setAnalysis(null); setResult(null); setError(null); setDownloaded(false); setDownloadPct(0);
        if (!f) return;
        setAnalyzing(true);
        try {
            const fd = new FormData(); fd.append("file", f);
            const r = await fetch(`${API}/api/v1/analyze`, { method: "POST", body: fd });
            if (!r.ok) throw new Error(await r.text());
            const a: Analysis = await r.json(); setAnalysis(a); setMode(a.recommended_mode);
        } catch (e: any) { setError("Analysis failed: " + e.message); }
        finally { setAnalyzing(false); }
    }

    async function startJob() {
        if (!file) return;
        setBusy(true); setError(null); setResult(null); setProgress(0); setDownloaded(false); setDownloadPct(0);
        try {
            const fd = new FormData(); fd.append("file", file); fd.append("mode", mode);
            const r = await fetch(`${API}/api/v1/compress`, { method: "POST", body: fd });
            if (!r.ok) throw new Error(await r.text());
            const { job_id } = await r.json();

            while (true) {
                const jr = await fetch(`${API}/api/v1/jobs/${job_id}`);
                const j = await jr.json(); setProgress(j.progress || 0);
                if (j.status === "completed") {
                    setResult(j.result); setBusy(false);
                    if (autoDownload && j.result) await doDownload(j.result, file);
                    break;
                }
                if (j.status === "failed") { setError("Failed: " + (j.message || "cancelled")); setBusy(false); break; }
                await new Promise(res => setTimeout(res, 300));
            }
        } catch (e: any) { setError(e.message); setBusy(false); }
    }

    async function doDownload(r: JobResult, sourceFile?: File) {
        const targetFile = sourceFile ?? file; if (!targetFile) return;
        setDownloading(true); setDownloadPct(0);
        try {
            const filename = suggestedFilename(targetFile.name, r.mode);
            const ok = await saveToDevice(`${API}${r.download_url}`, filename, (l, t) => { if (t > 0) setDownloadPct(Math.round((100 * l) / t)); });
            if (ok) setDownloaded(true);
        } catch (e: any) { setError("Download failed: " + e.message); } finally { setDownloading(false); }
    }

    async function handleRestore() {
        if (!restoreFile) return; setRestoring(true); setRestoreError(null);
        try {
            const fd = new FormData(); fd.append("file", restoreFile);
            const r = await fetch(`${API}/api/v1/restore`, { method: "POST", body: fd });
            if (!r.ok) throw new Error(await r.text());
            const blob = await r.blob(); const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a"); a.href = url; a.download = restoreFile.name.replace(/\.akp$/, "");
            document.body.appendChild(a); a.click(); a.remove(); window.URL.revokeObjectURL(url);
        } catch (e: any) { setRestoreError(e.message || "Failed to restore."); } finally { setRestoring(false); }
    }

    async function handleWatch() {
        if (!watchFile) return;
        setWatching(true); setWatchError(null); setVideoUrl(null); setSubtitleUrl(null); setWatchProgress(0);

        try {
            const decodedBlob = await decodeAkpInBrowser(watchFile, (pct) => setWatchProgress(pct));
            setVideoUrl(URL.createObjectURL(decodedBlob));
        } catch (e: any) {
            setWatchError(e.message || "Failed to decode video in browser.");
        } finally {
            setWatching(false);
        }
    }

    async function handleSubtitleUpload(e: React.ChangeEvent<HTMLInputElement>) {
        const subFile = e.target.files?.[0];
        if (!subFile) return;

        try {
            const text = await subFile.text();
            let vttContent = text;

            if (subFile.name.toLowerCase().endsWith('.srt')) {
                vttContent = convertSrtToVtt(text);
            }

            const vttBlob = new Blob([vttContent], { type: "text/vtt" });
            setSubtitleUrl(URL.createObjectURL(vttBlob));
        } catch (err) {
            alert("Failed to load subtitle file.");
        }
    }

    return (
        <div className="min-h-screen bg-[#0a1610] text-[#e5eedb] flex flex-col transition-colors duration-300">
            <Navbar />

            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-3xl mx-auto text-center px-6 pt-16 pb-10">
                <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight mb-4">
                    Compress. <span className="text-[#a3e635]">Restore.</span> Watch.
                </h1>
                <p className="text-[#8fa896] text-lg max-w-xl mx-auto">
                    Lossless compression for exact byte restoration, or AV1 transcoding for 50% smaller video.
                </p>
            </motion.div>

            <div className="flex-1 w-full max-w-5xl mx-auto px-6 pb-12">

                <div className="flex justify-center mb-6">
                    <div className="inline-flex bg-[#152219] rounded-lg p-1 border border-[#2d4a37]">
                        <button onClick={() => setActiveTab("compress")} className={`px-6 py-2 rounded-md text-sm font-semibold transition-all ${activeTab === "compress" ? "bg-[#2d4a37] text-white shadow-sm" : "text-[#8fa896] hover:text-white"}`}>Compress</button>
                        <button onClick={() => setActiveTab("restore")} className={`px-6 py-2 rounded-md text-sm font-semibold transition-all ${activeTab === "restore" ? "bg-[#2d4a37] text-white shadow-sm" : "text-[#8fa896] hover:text-white"}`}>Restore</button>
                        <button onClick={() => setActiveTab("watch")} className={`px-6 py-2 rounded-md text-sm font-semibold transition-all ${activeTab === "watch" ? "bg-[#2d4a37] text-white shadow-sm" : "text-[#8fa896] hover:text-white"}`}>Watch</button>
                    </div>
                </div>

                <div className="max-w-2xl mx-auto bg-[#152219] border border-[#2d4a37] rounded-2xl p-6 shadow-xl shadow-black/30 transition-colors">

                    {activeTab === "compress" && (
                        <div className="space-y-5">
                            <label className="block">
                                <span className="text-xs uppercase tracking-wider text-[#8fa896] mb-2 block">Choose a file to compress</span>
                                <input type="file" onChange={e => onSelectFile(e.target.files?.[0] ?? null)} className="block w-full text-sm text-[#c8d6be] file:mr-3 file:py-2.5 file:px-5 file:rounded-lg file:border-0 file:bg-[#4d7c0f] file:text-white file:font-medium file:cursor-pointer hover:file:bg-[#65a30d] file:transition-colors" />
                                {file && !analyzing && (
                                    <div className="text-xs text-[#8fa896] mt-3 flex flex-col gap-1">
                                        <span><span className="text-[#c8d6be] font-medium">{file.name}</span> · {formatBytes(file.size)}</span>
                                        <span className="text-[#a3e635]">Output: {suggestedFilename(file.name, mode)}</span>
                                    </div>
                                )}
                            </label>

                            {analyzing && <Loader text="Analyzing file" />}

                            {analysis && (
                                <div className="bg-[#1f3326] border border-[#2d4a37] rounded-xl p-4 space-y-4 shadow-sm">
                                    <div className="flex items-start gap-2">
                                        <span className="px-2 py-0.5 rounded-md bg-[#2d4a37] text-[#a3e635] text-[10px] font-semibold uppercase">{analysis.category}</span>
                                        {analysis.codec && <span className="px-2 py-0.5 rounded-md bg-[#2d4a37] text-[#a3e635] text-[10px] font-semibold uppercase">{analysis.codec}</span>}
                                    </div>
                                    <p className="text-sm text-[#c8d6be]">{analysis.reason}</p>
                                    <div className="grid grid-cols-2 gap-3">
                                        <button onClick={() => setMode("lossless")} className={`p-3 rounded-xl text-left transition-all ${mode === "lossless" ? "bg-[#4d7c0f] border-2 border-[#a3e635] text-white shadow-lg shadow-[#4d7c0f]/30" : "bg-[#152219] border-2 border-[#2d4a37] text-[#c8d6be] hover:border-[#4d7c0f]"}`}>
                                            <div className="font-semibold text-sm">Lossless</div>
                                            <div className="text-xs opacity-85 mt-0.5">~{analysis.lossless_expected_pct.toFixed(0)}% savings</div>
                                        </button>
                                        {analysis.transcode_expected_pct !== null && (
                                            ffmpegAvailable === false ? (
                                                <div className="p-3 rounded-xl bg-[#152219] border-2 border-[#2d4a37] opacity-60">
                                                    <div className="font-semibold text-sm text-[#8fa896]">AV1 (lossy)</div>
                                                    <div className="text-xs text-[#8fa896] mt-0.5">Server has no FFmpeg</div>
                                                </div>
                                            ) : (
                                                <button onClick={() => setMode("transcode")} className={`p-3 rounded-xl text-left transition-all ${mode === "transcode" ? "bg-[#65a30d] border-2 border-[#a3e635] text-white shadow-lg shadow-[#65a30d]/30" : "bg-[#152219] border-2 border-[#2d4a37] text-[#c8d6be] hover:border-[#65a30d]"}`}>
                                                    <div className="font-semibold text-sm">AV1 (lossy)</div>
                                                    <div className="text-xs opacity-85 mt-0.5">~{analysis.transcode_expected_pct.toFixed(0)}% savings</div>
                                                </button>
                                            )
                                        )}
                                    </div>
                                    <label className="flex items-start gap-3 cursor-pointer pt-3 border-t border-[#2d4a37]">
                                        <input type="checkbox" checked={autoDownload} onChange={e => setAutoDownload(e.target.checked)} className="mt-1 w-4 h-4 accent-[#84cc16] cursor-pointer" />
                                        <div>
                                            <div className="text-sm text-[#c8d6be] font-medium">Download automatically when done</div>
                                            <div className="text-xs text-[#8fa896]">Your browser will ask where to save the file.</div>
                                        </div>
                                    </label>
                                </div>
                            )}

                            <button onClick={startJob} disabled={!file || busy || analyzing || (mode === "transcode" && ffmpegAvailable === false)} className="w-full py-3.5 rounded-xl bg-[#84cc16] hover:bg-[#a3e635] disabled:bg-[#2d4a37] disabled:text-[#5a7565] text-[#0a1610] font-bold text-sm tracking-wide transition-all disabled:cursor-not-allowed shadow-lg shadow-[#84cc16]/20 disabled:shadow-none">
                                {busy ? `Processing… ${progress.toFixed(0)}%` : `Start ${mode === "lossless" ? "compression" : "transcode"}`}
                            </button>

                            {busy && (
                                <div className="space-y-2">
                                    <Loader text={mode === "transcode" ? "Encoding AV1" : "Compressing"} />
                                    <div className="w-full h-2.5 bg-[#0a1610] rounded-full overflow-hidden border border-[#2d4a37]">
                                        <div className="h-full bg-gradient-to-r from-[#4d7c0f] via-[#84cc16] to-[#a3e635] transition-all duration-300 rounded-full" style={{ width: `${progress}%` }} />
                                    </div>
                                </div>
                            )}

                            {error && <div className="bg-[#2a0a0a] border border-[#7f1d1d] rounded-lg p-3"><p className="text-sm text-[#fca5a5] break-words">{error}</p></div>}

                            {result && (
                                <div className="bg-gradient-to-br from-[#142a10] to-[#1f3326] border border-[#4d7c0f] rounded-xl p-4 space-y-3">
                                    <div className="flex items-center justify-between">
                                        <p className="text-sm font-semibold text-[#a3e635] flex items-center gap-2"><span className="w-6 h-6 rounded-full bg-[#4d7c0f] flex items-center justify-center text-xs text-white">✓</span>{result.savings_pct.toFixed(1)}% smaller</p>
                                        {downloaded && <span className="text-[10px] text-[#a3e635] bg-[#4d7c0f]/40 px-2 py-1 rounded-md font-medium uppercase tracking-wider">Saved</span>}
                                    </div>
                                    <div className="text-xs text-[#8fa896] space-y-1">
                                        <div className="flex justify-between"><span>Original</span><span className="text-[#c8d6be] font-mono">{formatBytes(result.orig_size)}</span></div>
                                        <div className="flex justify-between"><span>Output</span><span className="text-[#a3e635] font-mono">{formatBytes(result.compressed_size)}</span></div>
                                    </div>
                                    <button onClick={() => doDownload(result)} disabled={downloading} className="w-full mt-2 px-4 py-2.5 rounded-lg bg-[#4d7c0f] hover:bg-[#65a30d] disabled:opacity-50 text-white text-sm font-semibold transition-colors">
                                        {downloaded ? "Save again" : "Save to device"}
                                    </button>
                                </div>
                            )}

                            <div className="mt-6 bg-[#152219]/50 border border-[#2d4a37] border-dashed rounded-2xl p-5 text-center">
                                <h3 className="text-sm font-semibold text-[#e5eedb] mb-1">Need AV1 but using the free live web version?</h3>
                                <p className="text-xs text-[#8fa896] mb-3 max-w-md mx-auto">Cloud servers don't have the CPU for heavy video encoding. Download the free open-source CLI to transcode videos on your own laptop.</p>
                                <a href="https://github.com/iamthearafatkhan/akpack/releases/latest/download/AKPack-Tool.exe" target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#2d4a37] hover:bg-[#4d7c0f] text-white text-sm font-semibold transition-colors">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 .3a12 12 0 0 0-3.8 23.4c.6.1.8-.3.8-.6v-2.2c-3.3.7-4-1.6-4-1.6-.6-1.4-1.4-1.8-1.4-1.8-1.1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1.1 1.9 2.8 1.3 3.5 1 .1-.8.4-1.3.8-1.6-2.7-.3-5.5-1.3-5.5-5.9 0-1.3.5-2.4 1.2-3.2-.1-.3-.5-1.5.1-3.2 0 0 1-.3 3.3 1.2a11.5 11.5 0 0 1 6 0c2.3-1.5 3.3-1.2 3.3-1.2.6 1.7.2 2.9.1 3.2.8.8 1.2 1.9 1.2 3.2 0 4.6-2.8 5.6-5.5 5.9.4.4.8 1.1.8 2.2v3.2c0 .3.2.7.8.6A12 12 0 0 0 12 .3z" /></svg>
                                    Download CLI Tool (.exe)
                                </a>
                            </div>
                        </div>
                    )}

                    {activeTab === "restore" && (
                        <div className="space-y-5">
                            <label className="block">
                                <span className="text-xs uppercase tracking-wider text-[#8fa896] mb-2 block">Upload an .akp file to restore</span>
                                <input type="file" accept=".akp" onChange={e => setRestoreFile(e.target.files?.[0] ?? null)} className="block w-full text-sm text-[#c8d6be] file:mr-3 file:py-2.5 file:px-5 file:rounded-lg file:border-0 file:bg-[#4d7c0f] file:text-white file:font-medium file:cursor-pointer hover:file:bg-[#65a30d] file:transition-colors" />
                                {restoreFile && <span className="text-xs text-[#8fa896] mt-3 block"><span className="text-[#c8d6be] font-medium">{restoreFile.name}</span> · {formatBytes(restoreFile.size)}</span>}
                            </label>
                            <button onClick={handleRestore} disabled={!restoreFile || restoring} className="w-full py-3.5 rounded-xl bg-[#84cc16] hover:bg-[#a3e635] disabled:bg-[#2d4a37] disabled:text-[#5a7565] text-[#0a1610] font-bold text-sm tracking-wide transition-all shadow-lg shadow-[#84cc16]/20">
                                {restoring ? "Restoring..." : "Restore Original File"}
                            </button>
                            {restoring && <Loader text="Restoring exact file..." />}
                            {restoreError && <div className="bg-[#2a0a0a] border border-[#7f1d1d] rounded-lg p-3"><p className="text-sm text-[#fca5a5] break-words">{restoreError}</p></div>}
                        </div>
                    )}

                    {activeTab === "watch" && (
                        <div className="space-y-5">
                            <label className="block">
                                <span className="text-xs uppercase tracking-wider text-[#8fa896] mb-2 block">Upload an .akp file to watch instantly</span>
                                <input type="file" accept=".akp" onChange={e => { setWatchFile(e.target.files?.[0] ?? null); setVideoUrl(null); setSubtitleUrl(null); }} className="block w-full text-sm text-[#c8d6be] file:mr-3 file:py-2.5 file:px-5 file:rounded-lg file:border-0 file:bg-[#4d7c0f] file:text-white file:font-medium file:cursor-pointer hover:file:bg-[#65a30d] file:transition-colors" />
                                {watchFile && <span className="text-xs text-[#8fa896] mt-3 block"><span className="text-[#c8d6be] font-medium">{watchFile.name}</span> · {formatBytes(watchFile.size)}</span>}
                            </label>

                            <button onClick={handleWatch} disabled={!watchFile || watching} className="w-full py-3.5 rounded-xl bg-[#84cc16] hover:bg-[#a3e635] disabled:bg-[#2d4a37] disabled:text-[#5a7565] text-[#0a1610] font-bold text-sm tracking-wide transition-all shadow-lg shadow-[#84cc16]/20">
                                {watching ? `Decoding in browser... ${watchProgress}%` : "Extract & Play Video"}
                            </button>

                            {watchError && <div className="bg-[#2a0a0a] border border-[#7f1d1d] rounded-lg p-3"><p className="text-sm text-[#fca5a5] break-words">{watchError}</p></div>}

                            {watching && (
                                <div className="space-y-2">
                                    <div className="w-full h-2.5 bg-[#0a1610] rounded-full overflow-hidden border border-[#2d4a37]">
                                        <div className="h-full bg-gradient-to-r from-[#4d7c0f] via-[#84cc16] to-[#a3e635] transition-all duration-300 rounded-full" style={{ width: `${watchProgress}%` }} />
                                    </div>
                                </div>
                            )}

                            {videoUrl && (
                                <div className="space-y-4 mt-4">
                                    {/* Subtitle Upload Area */}
                                    <div className="bg-[#1f3326] border border-[#2d4a37] rounded-xl p-4 flex items-center justify-between">
                                        <div>
                                            <h3 className="text-sm font-semibold text-[#e5eedb]">Subtitles</h3>
                                            <p className="text-xs text-[#8fa896]">Upload a .srt or .vtt file to display on the video.</p>
                                        </div>
                                        <label className="cursor-pointer bg-[#4d7c0f] hover:bg-[#65a30d] text-white text-xs font-semibold py-2 px-4 rounded-lg transition-colors">
                                            Upload File
                                            <input type="file" accept=".srt,.vtt" onChange={handleSubtitleUpload} className="hidden" />
                                        </label>
                                    </div>

                                    {/* Video Player with Native Fullscreen Subtitles */}
                                    <div className="rounded-xl overflow-hidden border border-[#2d4a37] bg-black shadow-lg">
                                        <video src={videoUrl} controls autoPlay className="w-full max-h-[600px] object-contain" crossOrigin="anonymous">
                                            {subtitleUrl && (
                                                <track kind="subtitles" src={subtitleUrl} srcLang="en" label="English" default />
                                            )}
                                        </video>
                                    </div>
                                    {subtitleUrl && (
                                        <p className="text-xs text-[#a3e635] text-center">Subtitle loaded! Click the fullscreen button on the video to watch.</p>
                                    )}
                                </div>
                            )}
                        </div>
                    )}

                </div>
            </div>
            <Footer />
        </div>
    );
}

export default function App() {
    return (
        <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/faq" element={<FAQ />} />
            <Route path="/privacy" element={<Privacy />} />
            <Route path="/terms" element={<Terms />} />
        </Routes>
    );
}