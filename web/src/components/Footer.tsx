import { Link } from "react-router-dom";

export default function Footer() {
    return (
        <footer className="w-full border-t border-[#2d4a37] bg-[#0a1610] py-8 mt-auto transition-colors">
            <div className="max-w-5xl mx-auto px-6 flex flex-col items-center justify-between gap-6 sm:flex-row text-sm text-[#8fa896]">

                {/* Left: Built by */}
                <div className="flex-1 text-center sm:text-left">
                    <p className="text-sm">
                        Built by <span className="font-semibold text-[#e5eedb]">Arafat Khan</span>
                    </p>
                </div>

                {/* Middle: Socials */}
                <div className="flex flex-1 items-center justify-center gap-6">
                    <a href="https://linkedin.com/in/iamthearafatkhan" target="_blank" rel="noopener noreferrer" className="hover:text-[#a3e635] hover:-translate-y-1 transition-all">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M20.45 20.45h-3.55v-5.57c0-1.33-.03-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0 0 1 0 4.13zm1.78 13.02H3.55V9h3.57v11.45zM22.22 0H1.77C.79 0 0 .77 0 1.73v20.54C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.2 0 22.22 0z" /></svg>
                    </a>
                    <a href="https://github.com/iamthearafatkhan" target="_blank" rel="noopener noreferrer" className="hover:text-[#a3e635] hover:-translate-y-1 transition-all">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 .3a12 12 0 0 0-3.8 23.4c.6.1.8-.3.8-.6v-2.2c-3.3.7-4-1.6-4-1.6-.6-1.4-1.4-1.8-1.4-1.8-1.1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1.1 1.9 2.8 1.3 3.5 1 .1-.8.4-1.3.8-1.6-2.7-.3-5.5-1.3-5.5-5.9 0-1.3.5-2.4 1.2-3.2-.1-.3-.5-1.5.1-3.2 0 0 1-.3 3.3 1.2a11.5 11.5 0 0 1 6 0c2.3-1.5 3.3-1.2 3.3-1.2.6 1.7.2 2.9.1 3.2.8.8 1.2 1.9 1.2 3.2 0 4.6-2.8 5.6-5.5 5.9.4.4.8 1.1.8 2.2v3.2c0 .3.2.7.8.6A12 12 0 0 0 12 .3z" /></svg>
                    </a>
                    <a href="https://arafatkhan.vercel.app" target="_blank" rel="noopener noreferrer" className="hover:opacity-80 hover:-translate-y-1 transition-all">
                        <img src="./web/img/ak-logo.png" alt="AK Website" width="22" height="22" className="rounded-md object-contain bg-white/10 p-0.5" />
                    </a>
                </div>

                {/* Right: FAQ & Privacy (Stacked) */}
                <div className="flex flex-1 flex-col items-center sm:items-end gap-2 text-sm font-medium">
                    <Link to="/faq" className="hover:text-[#a3e635] transition-colors">FAQ</Link>
                    <Link to="/privacy" className="hover:text-[#a3e635] transition-colors">Privacy</Link>
                </div>

            </div>
        </footer>
    );
}
