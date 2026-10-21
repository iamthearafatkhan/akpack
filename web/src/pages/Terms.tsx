import Navbar from "../components/Navbar";
import Footer from "../components/Footer";

export default function Terms() {
    return (
        <div className="min-h-screen bg-[#0a1610] text-[#e5eedb] flex flex-col transition-colors">
            <Navbar />
            <div className="flex-1 max-w-3xl mx-auto space-y-6 px-6 py-12 w-full">
                <h1 className="text-3xl font-bold text-[#a3e635]">Terms of Service</h1>

                <div className="bg-[#152219] border border-[#2d4a37] p-6 rounded-xl space-y-4 text-sm text-[#8fa896] leading-relaxed">
                    <p><strong>Last updated: October 2026</strong></p>

                    <h2 className="text-lg font-semibold text-[#e5eedb] mt-6 mb-2">1. Acceptance of Terms</h2>
                    <p>By using AKPack, you agree to these Terms. If you do not agree, please do not use the service.</p>

                    <h2 className="text-lg font-semibold text-[#e5eedb] mt-6 mb-2">2. Acceptable Use</h2>
                    <p>You agree not to use AKPack to compress, distribute, or process illegal content, including but not limited to copyrighted material without authorization, malware, or explicit illegal material. You are solely responsible for the files you process.</p>

                    <h2 className="text-lg font-semibold text-[#e5eedb] mt-6 mb-2">3. No File Storage / Copyright</h2>
                    <p>AKPack operates primarily as a local processing tool. When you use the "Watch" feature, the video is decoded entirely within your browser and is never uploaded to or stored on our servers. We do not host, store, or distribute video files. We comply with the Digital Millennium Copyright Act (DMCA) and will cooperate with authorities regarding illegal activity.</p>

                    <h2 className="text-lg font-semibold text-[#e5eedb] mt-6 mb-2">4. Disclaimer of Warranty</h2>
                    <p>AKPack is provided "as is" without warranty of any kind. We are not responsible for data loss, corrupted files, or any damages resulting from the use of this software.</p>
                </div>
            </div>
            <Footer />
        </div>
    );
}