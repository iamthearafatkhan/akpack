import Navbar from "../components/Navbar";
import Footer from "../components/Footer";

export default function Privacy() {
    return (
        <div className="min-h-screen bg-[#0a1610] text-[#e5eedb] flex flex-col transition-colors">
            <Navbar />
            <div className="flex-1 max-w-3xl mx-auto space-y-6 px-6 py-12 w-full">
                <h1 className="text-3xl font-bold text-[#a3e635]">Privacy Policy</h1>

                <div className="bg-[#152219] border border-[#2d4a37] p-6 rounded-xl space-y-4 text-sm text-[#8fa896] leading-relaxed">
                    <p><strong>Last updated: October 2026</strong></p>
                    <p>At AKPack, we believe in honesty and transparency. Here is exactly what happens to your files:</p>

                    <ul className="list-disc pl-5 space-y-3 mt-4">
                        <li>
                            <strong>Watch Mode (Client-Side):</strong> When you use the "Watch" tab on our website, your `.akp` file is decoded entirely within your own browser using WebAssembly (WASM). <strong>The file is never uploaded to, stored on, or processed by our servers.</strong> Your video remains 100% private on your device.
                        </li>
                        <li>
                            <strong>Lossless & AV1 Compression (Server-Side):</strong> To compress files or transcode to AV1 on the web, the file is temporarily uploaded to our processing server. We do not inspect, share, or sell your data. Files are processed in memory and temporary disk space, and are automatically deleted immediately after processing.
                        </li>
                        <li>
                            <strong>AKPack Studio (Desktop App):</strong> Our desktop application processes all files locally on your machine. No internet connection is required to compress, restore, or play files in the desktop app.
                        </li>
                        <li>
                            <strong>No Tracking:</strong> We do not use invasive trackers, analytics scripts, or sell your personal data to advertisers.
                        </li>
                    </ul>
                </div>
            </div>
            <Footer />
        </div>
    );
}