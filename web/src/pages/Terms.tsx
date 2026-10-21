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
                    <p>By accessing or using AKPack (the "Service"), you agree to be bound by these Terms. If you do not agree to these Terms, you may not use the Service.</p>

                    <h2 className="text-lg font-semibold text-[#e5eedb] mt-6 mb-2">2. Nature of the Service (Local Processing)</h2>
                    <p>AKPack is a client-side, local-processing utility. When you use the "Watch" or "Restore" features, the `.akp` archive is decompressed and decoded entirely within your web browser using WebAssembly (WASM). <strong>We do not upload, host, store, or transmit the decoded contents of your video or data files to our servers.</strong></p>

                    <h2 className="text-lg font-semibold text-[#e5eedb] mt-6 mb-2">3. Acceptable Use & User Responsibility</h2>
                    <p>You agree to use AKPack only for lawful purposes. You are solely responsible for ensuring that you have the legal right to process, compress, or view any file you use with this Service.</p>
                    <ul className="list-disc pl-5 mt-2 space-y-1">
                        <li>You may not use AKPack to process, distribute, or facilitate the distribution of copyrighted material without explicit authorization from the rights holder.</li>
                        <li>You may not use AKPack to process malware, illegal content, or material that violates any applicable law.</li>
                        <li><strong>Renaming or altering file names</strong> (e.g., renaming a copyrighted movie to "123.mp4.akp") does not bypass copyright law or these Terms. You remain fully liable for the content you process.</li>
                    </ul>

                    <h2 className="text-lg font-semibold text-[#e5eedb] mt-6 mb-2">4. DMCA & Copyright Policy</h2>
                    <p>We respect the intellectual property rights of others. Because AKPack does not host or store user files, we are protected under the Digital Millennium Copyright Act (DMCA) Safe Harbor provisions. However, we strictly prohibit the use of our tool for infringement. If you believe your copyrighted work has been used in a way that constitutes copyright infringement, please contact us immediately at <strong>abuse@akpack.pages.dev</strong> with the subject line "DMCA Takedown." We will investigate and cooperate fully with law enforcement regarding illegal activity.</p>

                    <h2 className="text-lg font-semibold text-[#e5eedb] mt-6 mb-2">5. Indemnification</h2>
                    <p>You agree to indemnify, defend, and hold harmless AKPack, its developers, and affiliates from and against any and all claims, damages, obligations, losses, liabilities, costs, or debt, and expenses (including but not limited to attorney's fees) arising from your use of the Service or your violation of these Terms.</p>

                    <h2 className="text-lg font-semibold text-[#e5eedb] mt-6 mb-2">6. Disclaimer of Warranty</h2>
                    <p>AKPack is provided "as is" and "as available" without warranties of any kind, either express or implied. We do not guarantee that the Service will be uninterrupted, secure, or error-free. We are not responsible for data loss, corrupted files, or any damages resulting from the use of this software.</p>

                    <h2 className="text-lg font-semibold text-[#e5eedb] mt-6 mb-2">7. Modifications to Service</h2>
                    <p>We reserve the right to modify or discontinue, temporarily or permanently, the Service (or any part thereof) with or without notice. We shall not be liable to you or any third party for any modification, suspension, or discontinuance of the Service.</p>
                </div>
            </div>
            <Footer />
        </div>
    );
}