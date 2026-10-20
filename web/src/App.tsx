import { useEffect, useState } from "react";
import { Routes, Route } from "react-router-dom";
import { motion } from "framer-motion";
import { API } from "./lib/api";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import FAQ from "./pages/FAQ";
import Privacy from "./pages/Privacy";
import Loader from "./components/Loader";

type Analysis = {
    category: string;
    recommended_mode: "lossless" | "transcode";
    reason: string;
    lossless_expected_pct: number;
    transcode_expected_pct: number | null;
    duration_s?: number | null;
    codec?: string | null;
};
type JobResult = {
    archive_id: string;
    mode: "lossless" | "transcode";
    orig_size: number;
    compressed_size: number;
    savings_pct: number;
    download_url: string;
    warning?: string;
};
function formatBytes(n: number): string {
    if (n < 1024) return `${n} B`;
    if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
    if (n < 1024 * 1024 * 1024) return `${(n / (1024 * 1024)).toFixed(1)} MB`;
    return `${(n / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}
function suggestedFilename(original: string, mode: "lossless" | "transcode"): string {
    if (mode === "transcode") {
        const base = original.replace(/\.[^.]+$/, "");
        return `${base}.av1.mp4`;
    }
    return `${original}.akp`; // Always appends .akp for lossless
}
async function saveToDevice(url: string, filename: string, onProgress?: (loaded: number, total: number) => void): Promise<boolean> {
    if ("showSaveFilePicker" in window) {
        try {
            const handle = await (window as any).showSaveFilePicker({ suggestedName: filename });
            const writable = await handle.createWritable();
            const resp = await fetch(url);
            if (!resp.ok) throw new Error(`Download failed (${resp.status})`);
            const total = parseInt(resp.headers.get("content-length") || "0", 10);
            let loaded = 0;
            const reader = resp.body?.getReader();
            if (!reader) throw new Error("No response body");
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                await writable.write(value);
                loaded += value.length;
                onProgress?.(loaded, total);
            }
            await writable.close();
            return true;
        } catch (e: any) {
            if (e.name === "AbortError") return false;
        }
    }
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    return true;
}

function Home() {
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
            const a: Analysis = await r.json();
            setAnalysis(a); setMode(a.recommended_mode);
        } catch (e: any) { setError("Analysis failed: " + e.message); }
        finally { setAnalyzing(false); }
    }

    async function startJob() {
        if (!file) return;
        const currentFile = file;
        setBusy(true); setError(null); setResult(null); setProgress(0); setDownloaded(false); setDownloadPct(0);
        try {
            const fd = new FormData(); fd.append("file", currentFile); fd.append("mode", mode);
            const r = await fetch(`${API}/api/v1/compress`, { method: "POST", body: fd });
            if (!r.ok) throw new Error(await r.text());
            const { job_id } = await r.json();

            // Pass job_id directly to pollJob to avoid React state delay bugs
            await pollJob(job_id, currentFile);
        } catch (e: any) { setError(e.message); setBusy(false); }
    }

    async function cancelJob() {
        // We don't need to manually track jobId in state anymore for polling,
        // but we do need it to send the cancel request.
        setBusy(false);
        setError("Job cancelled.");
        // The pollJob loop will break when the server reports "failed"
    }

    async function pollJob(id: string, sourceFile: File) {
        while (true) {
            const r = await fetch(`${API}/api/v1/jobs/${id}`);
            if (!r.ok) { setError("Job lookup failed"); setBusy(false); return; }
            const j = await r.json();
            setProgress(j.progress || 0);

            if (j.status === "completed") {
                setResult(j.result); setBusy(false);
                if (autoDownload && j.result) await doDownload(j.result, sourceFile);
                return;
            }
            if (j.status === "failed") {
                setError("Processing failed: " + (j.message || "cancelled"));
                setBusy(false); return;
            }
            await new Promise(res => setTimeout(res, 500)); // Poll every 500ms for faster feedback
        }
    }

    async function doDownload(r: JobResult, sourceFile?: File) {
        const targetFile = sourceFile ?? file;
        if (!targetFile) return;
        setDownloading(true); setDownloadPct(0);
        try {
            const filename = suggestedFilename(targetFile.name, r.mode);
            const ok = await saveToDevice(`${API}${r.download_url}`, filename, (loaded, total) => {
                if (total > 0) setDownloadPct(Math.round((100 * loaded) / total));
            });
            if (ok) setDownloaded(true);
        } catch (e: any) { setError("Download failed: " + e.message); }
        finally { setDownloading(false); }
    }

    const transcodeDisabled = mode === "transcode" && ffmpegAvailable === false;

    return (
        <div className="min-h-screen bg-white dark:bg-[#0a1610] text-gray-900 dark:text-[#e5eedb] transition-colors duration-300">
            <Navbar />

            <motion.div
                initial="hidden" animate="visible"
                variants={{ hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.2 } } }}
                className="max-w-3xl mx-auto text-center px-6 pt-20 pb-12"
            >
                <motion.div variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } } }}>
                    <span className="inline-block py-1 px-3 rounded-full bg-[#e5eedb] dark:bg-[#152219] text-[#4d7c0f] dark:text-[#a3e635] text-xs font-bold tracking-widest uppercase mb-6 border border-[#a3e635]/30 shadow-sm">
                        v1.0 is live
                    </span>
                </motion.div>

                <motion.h1
                    variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } } }}
                    className="text-4xl md:text-6xl font-extrabold tracking-tight mb-6"
                >
                    Compress files.<br />
                    <span className="text-[#4d7c0f] dark:text-[#a3e635]">Keep the quality.</span>
                </motion.h1>

                <motion.p
                    variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } } }}
                    className="text-gray-600 dark:text-[#8fa896] text-lg max-w-xl mx-auto leading-relaxed"
                >
                    Lossless compression for exact byte restoration, or AV1 transcoding for 50% smaller video. No lies, no hidden quality drops.
                </motion.p>
            </motion.div>

            <div className="max-w-2xl mx-auto px-6 pb-12 relative z-10">
                <div className="bg-gray-50 dark:bg-[#152219] border border-gray-200 dark:border-[#2d4a37] rounded-2xl p-6 space-y-5 shadow-xl shadow-gray-200/50 dark:shadow-black/30 transition-colors">
                    <label className="block">
                        <span className="text-xs uppercase tracking-wider text-gray-500 dark:text-[#8fa896] mb-2 block">Choose a file</span>
                        <input type="file" onChange={e => onSelectFile(e.target.files?.[0] ?? null)}
                            className="block w-full text-sm text-gray-600 dark:text-[#c8d6be] file:mr-3 file:py-2.5 file:px-5 file:rounded-lg file:border-0 file:bg-[#4d7c0f] file:text-white file:font-medium file:cursor-pointer hover:file:bg-[#65a30d] file:transition-colors"
                        />
                        {file && !analyzing && (
                            <div className="text-xs text-gray-500 dark:text-[#8fa896] mt-3 flex flex-col gap-1">
                                <span><span className="text-gray-900 dark:text-[#c8d6be] font-medium">{file.name}</span> · {formatBytes(file.size)}</span>
                                <span className="text-[#4d7c0f] dark:text-[#a3e635]">Output: {suggestedFilename(file.name, mode)}</span>
                            </div>
                        )}
                    </label>

                    {analyzing && <Loader text="Analyzing file" />}

                    {analysis && (
                        <div className="bg-white dark:bg-[#1f3326] border border-gray-200 dark:border-[#2d4a37] rounded-xl p-4 space-y-4 shadow-sm transition-colors">
                            <div className="flex items-start gap-2">
                                <span className="px-2 py-0.5 rounded-md bg-gray-100 dark:bg-[#2d4a37] text-[#4d7c0f] dark:text-[#a3e635] text-[10px] font-semibold uppercase">{analysis.category}</span>
                                {analysis.codec && <span className="px-2 py-0.5 rounded-md bg-gray-100 dark:bg-[#2d4a37] text-[#4d7c0f] dark:text-[#a3e635] text-[10px] font-semibold uppercase">{analysis.codec}</span>}
                            </div>
                            <p className="text-sm text-gray-700 dark:text-[#c8d6be]">{analysis.reason}</p>
                            <div className="grid grid-cols-2 gap-3">
                                <button onClick={() => setMode("lossless")}
                                    className={`p-3 rounded-xl text-left transition-all ${mode === "lossless" ? "bg-[#4d7c0f] border-2 border-[#a3e635] text-white shadow-lg shadow-[#4d7c0f]/30" : "bg-gray-50 dark:bg-[#152219] border-2 border-gray-200 dark:border-[#2d4a37] text-gray-600 dark:text-[#c8d6be] hover:border-[#4d7c0f]"}`}
                                >
                                    <div className="font-semibold text-sm">Lossless</div>
                                    <div className="text-xs opacity-85 mt-0.5">~{analysis.lossless_expected_pct.toFixed(0)}% savings</div>
                                </button>
                                {analysis.transcode_expected_pct !== null && (
                                    ffmpegAvailable === false ? (
                                        <div className="p-3 rounded-xl bg-gray-50 dark:bg-[#152219] border-2 border-gray-200 dark:border-[#2d4a37] opacity-60">
                                            <div className="font-semibold text-sm text-gray-400 dark:text-[#8fa896]">AV1 (lossy)</div>
                                            <div className="text-xs text-gray-400 dark:text-[#8fa896] mt-0.5">Server has no FFmpeg</div>
                                        </div>
                                    ) : (
                                        <button onClick={() => setMode("transcode")}
                                            className={`p-3 rounded-xl text-left transition-all ${mode === "transcode" ? "bg-[#65a30d] border-2 border-[#a3e635] text-white shadow-lg shadow-[#65a30d]/30" : "bg-gray-50 dark:bg-[#152219] border-2 border-gray-200 dark:border-[#2d4a37] text-gray-600 dark:text-[#c8d6be] hover:border-[#65a30d]"}`}
                                        >
                                            <div className="font-semibold text-sm">AV1 (lossy)</div>
                                            <div className="text-xs opacity-85 mt-0.5">~{analysis.transcode_expected_pct.toFixed(0)}% savings</div>
                                        </button>
                                    )
                                )}
                            </div>
                            {mode === "transcode" && analysis.duration_s && (
                                <div className="flex gap-2 text-xs text-[#d97706] dark:text-[#fbbf24] bg-orange-50 dark:bg-[#2a1a08] border border-orange-200 dark:border-[#4a2c10] rounded-lg p-2.5">
                                    <span>⏱</span><span>Encoding takes ~{Math.max(1, Math.round(analysis.duration_s / 30))} min on CPU.</span>
                                </div>
                            )}
                            <label className="flex items-start gap-3 cursor-pointer pt-3 border-t border-gray-200 dark:border-[#2d4a37]">
                                <input type="checkbox" checked={autoDownload} onChange={e => setAutoDownload(e.target.checked)} className="mt-1 w-4 h-4 accent-[#84cc16] cursor-pointer" />
                                <div>
                                    <div className="text-sm text-gray-900 dark:text-[#c8d6be] font-medium">Download automatically when done</div>
                                    <div className="text-xs text-gray-500 dark:text-[#8fa896]">Your browser will ask where to save the file.</div>
                                </div>
                            </label>
                        </div>
                    )}

                    <div className="flex gap-3">
                        <button onClick={startJob} disabled={!file || busy || analyzing || transcodeDisabled}
                            className="flex-1 py-3.5 rounded-xl bg-[#84cc16] hover:bg-[#a3e635] disabled:bg-gray-300 dark:disabled:bg-[#2d4a37] disabled:text-gray-500 dark:disabled:text-[#5a7565] text-[#0a1610] font-bold text-sm tracking-wide transition-all disabled:cursor-not-allowed shadow-lg shadow-[#84cc16]/20 disabled:shadow-none"
                        >
                            {busy ? `Processing… ${progress.toFixed(0)}%` : `Start ${mode === "lossless" ? "compression" : "transcode"}`}
                        </button>
                        {busy && (
                            <button onClick={cancelJob}
                                className="px-6 py-3.5 rounded-xl bg-red-100 dark:bg-red-900/40 border border-red-300 dark:border-red-800 hover:bg-red-200 dark:hover:bg-red-900/60 text-red-600 dark:text-red-300 font-bold text-sm transition-all"
                            >
                                Cancel
                            </button>
                        )}
                    </div>

                    {busy && (
                        <div className="space-y-2">
                            <Loader text={mode === "transcode" ? "Encoding AV1" : "Compressing"} />
                            <div className="w-full h-2.5 bg-gray-200 dark:bg-[#0a1610] rounded-full overflow-hidden border border-gray-300 dark:border-[#2d4a37]">
                                <div className="h-full bg-gradient-to-r from-[#4d7c0f] via-[#84cc16] to-[#a3e635] transition-all duration-300 rounded-full" style={{ width: `${progress}%` }} />
                            </div>
                        </div>
                    )}

                    {downloading && (
                        <div className="space-y-2">
                            <div className="w-full h-2 bg-gray-200 dark:bg-[#0a1610] rounded-full overflow-hidden border border-gray-300 dark:border-[#2d4a37]">
                                <div className="h-full bg-gradient-to-r from-[#4d7c0f] to-[#a3e635] transition-all" style={{ width: `${downloadPct}%` }} />
                            </div>
                            <p className="text-xs text-gray-500 dark:text-[#8fa896] text-center">Saving to your device… {downloadPct > 0 ? `${downloadPct}%` : ""}</p>
                        </div>
                    )}

                    {error && <div className="bg-red-50 dark:bg-[#2a0a0a] border border-red-200 dark:border-[#7f1d1d] rounded-lg p-3"><p className="text-sm text-red-600 dark:text-[#fca5a5] break-words">{error}</p></div>}

                    {result && (
                        <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-[#142a10] dark:to-[#1f3326] border border-green-200 dark:border-[#4d7c0f] rounded-xl p-4 space-y-3">
                            <div className="flex items-center justify-between">
                                <p className="text-sm font-semibold text-[#4d7c0f] dark:text-[#a3e635] flex items-center gap-2"><span className="w-6 h-6 rounded-full bg-[#84cc16] dark:bg-[#4d7c0f] flex items-center justify-center text-xs text-white">✓</span>{result.savings_pct.toFixed(1)}% smaller</p>
                                {downloaded && <span className="text-[10px] text-[#4d7c0f] dark:text-[#a3e635] bg-[#a3e635]/20 dark:bg-[#4d7c0f]/40 px-2 py-1 rounded-md font-medium uppercase tracking-wider">Saved</span>}
                            </div>
                            <div className="text-xs text-gray-600 dark:text-[#8fa896] space-y-1">
                                <div className="flex justify-between"><span>Original</span><span className="text-gray-900 dark:text-[#c8d6be] font-mono">{formatBytes(result.orig_size)}</span></div>
                                <div className="flex justify-between"><span>Output</span><span className="text-[#4d7c0f] dark:text-[#a3e635] font-mono">{formatBytes(result.compressed_size)}</span></div>
                            </div>
                            {result.warning && <p className="text-xs text-[#d97706] dark:text-[#fbbf24] bg-orange-100 dark:bg-[#2a1a08] border border-orange-200 dark:border-[#4a2c10] rounded p-2">⚠ {result.warning}</p>}
                            <div className="flex gap-2 pt-1">
                                <button onClick={() => doDownload(result)} disabled={downloading}
                                    className="flex-1 px-4 py-2.5 rounded-lg bg-[#4d7c0f] hover:bg-[#65a30d] disabled:opacity-50 text-white text-sm font-semibold transition-colors"
                                >
                                    {downloaded ? "Save again" : "Save to device"}
                                </button>
                            </div>
                            {result.mode === "transcode" && (
                                <div className="pt-2 border-t border-gray-200 dark:border-[#2d4a37]">
                                    <p className="text-[10px] uppercase tracking-wider text-gray-500 dark:text-[#8fa896] mb-2">Preview</p>
                                    <video controls preload="metadata" src={`${API}${result.download_url}`} className="w-full rounded-lg border border-gray-300 dark:border-[#2d4a37] bg-black" />
                                </div>
                            )}
                        </div>
                    )}
                </div>

                <div className="mt-8 bg-gray-50 dark:bg-[#152219]/50 border border-gray-300 dark:border-[#2d4a37] border-dashed rounded-2xl p-6 text-center transition-colors">
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-[#e5eedb] mb-2">Need AV1 but using the free live web version?</h3>
                    <p className="text-xs text-gray-500 dark:text-[#8fa896] mb-4 max-w-md mx-auto">Cloud servers don't have the CPU for heavy video encoding. Download the free open-source CLI to transcode videos on your own laptop.</p>
                    <a href="https://github.com/iamthearafatkhan/akpack" target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-gray-200 dark:bg-[#2d4a37] hover:bg-[#4d7c0f] dark:hover:bg-[#4d7c0f] text-gray-900 dark:text-white text-sm font-semibold transition-colors">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 .3a12 12 0 0 0-3.8 23.4c.6.1.8-.3.8-.6v-2.2c-3.3.7-4-1.6-4-1.6-.6-1.4-1.4-1.8-1.4-1.8-1.1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1.1 1.9 2.8 1.3 3.5 1 .1-.8.4-1.3.8-1.6-2.7-.3-5.5-1.3-5.5-5.9 0-1.3.5-2.4 1.2-3.2-.1-.3-.5-1.5.1-3.2 0 0 1-.3 3.3 1.2a11.5 11.5 0 0 1 6 0c2.3-1.5 3.3-1.2 3.3-1.2.6 1.7.2 2.9.1 3.2.8.8 1.2 1.9 1.2 3.2 0 4.6-2.8 5.6-5.5 5.9.4.4.8 1.1.8 2.2v3.2c0 .3.2.7.8.6A12 12 0 0 0 12 .3z" /></svg>
                        Download CLI via GitHub
                    </a>
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
        </Routes>
    );
}