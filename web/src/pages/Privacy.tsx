import Navbar from "../components/Navbar";
import Footer from "../components/Footer";

export default function Privacy() {
    return (
        <div className="min-h-screen bg-white dark:bg-[#0a1610] text-gray-900 dark:text-[#e5eedb] flex flex-col transition-colors">
            <Navbar />
            <div className="flex-1 max-w-3xl mx-auto space-y-6 px-6 py-12 w-full">
                <h1 className="text-3xl font-bold text-[#4d7c0f] dark:text-[#a3e635]">Privacy Policy</h1>

                <div className="bg-gray-50 dark:bg-[#152219] border border-gray-200 dark:border-[#2d4a37] p-6 rounded-xl space-y-4 text-sm text-gray-600 dark:text-[#8fa896] leading-relaxed transition-colors">
                    <p><strong>Last updated: October 2026</strong></p>
                    <p>At AKPack, we believe in honesty and transparency. Here is exactly what happens to your files:</p>
                    <ul className="list-disc pl-5 space-y-2 mt-4">
                        <li><strong>Lossless Mode:</strong> Your file is compressed and stored temporarily on our server for you to download. It is not inspected, shared, or sold.</li>
                        <li><strong>AV1 Transcode Mode:</strong> To transcode, the video must be read by our server. We do not keep copies of your videos after the transcode is complete.</li>
                        <li><strong>Data Retention:</strong> All temporary files are automatically deleted from our servers every 24 hours to protect your privacy.</li>
                        <li><strong>No Tracking:</strong> We do not use invasive trackers or sell your personal data to advertisers.</li>
                    </ul>
                </div>
            </div>
            <Footer />
        </div>
    );
}