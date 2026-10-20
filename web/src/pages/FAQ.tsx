import { Link } from "react-router-dom";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";

export default function FAQ() {
    return (
        <div className="min-h-screen bg-white dark:bg-[#0a1610] text-gray-900 dark:text-[#e5eedb] flex flex-col transition-colors">
            <Navbar />
            <div className="flex-1 max-w-3xl mx-auto space-y-6 px-6 py-12 w-full">
                <h1 className="text-3xl font-bold text-[#4d7c0f] dark:text-[#a3e635]">Frequently Asked Questions</h1>

                <div className="space-y-6 mt-8">
                    <div className="bg-gray-50 dark:bg-[#152219] border border-gray-200 dark:border-[#2d4a37] p-6 rounded-xl transition-colors">
                        <h3 className="font-semibold text-gray-900 dark:text-[#e5eedb] mb-2">Why doesn't my MP4 shrink in Lossless mode?</h3>
                        <p className="text-gray-600 dark:text-[#8fa896] text-sm leading-relaxed">Video files (MP4, MKV) are already highly compressed using H.264 or H.265. Trying to compress them losslessly is like trying to squeeze water out of a wet sponge. You will only save 0–2%. To shrink video, use the AV1 mode.</p>
                    </div>

                    <div className="bg-gray-50 dark:bg-[#152219] border border-gray-200 dark:border-[#2d4a37] p-6 rounded-xl transition-colors">
                        <h3 className="font-semibold text-gray-900 dark:text-[#e5eedb] mb-2">Is AV1 lossless?</h3>
                        <p className="text-gray-600 dark:text-[#8fa896] text-sm leading-relaxed">No. AV1 is a modern video codec that re-encodes your video. It is "visually near-identical" (most people can't tell the difference), but it is not bit-for-bit identical. It usually reduces file size by 40–60%.</p>
                    </div>

                    <div className="bg-gray-50 dark:bg-[#152219] border border-gray-200 dark:border-[#2d4a37] p-6 rounded-xl transition-colors">
                        <h3 className="font-semibold text-gray-900 dark:text-[#e5eedb] mb-2">Why isn't AV1 working on the live website?</h3>
                        <p className="text-gray-600 dark:text-[#8fa896] text-sm leading-relaxed">AV1 encoding is CPU-intensive and requires FFmpeg. Free cloud servers cannot handle it. If you see "Server has no FFmpeg", you can download our CLI tool and run AV1 transcoding locally on your own laptop for free.</p>
                    </div>
                </div>
            </div>
            <Footer />
        </div>
    );
}