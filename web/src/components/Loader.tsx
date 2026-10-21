export default function Loader({ text }: { text: string }) {
    return (
        <div className="flex flex-col items-center justify-center py-12 space-y-5">
            <div className="relative flex items-center justify-center w-24 h-24">
                {/* Background track ring */}
                <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="46" fill="none" stroke="#2d4a37" strokeWidth="4" />
                </svg>

                {/* Perfectly smooth spinning ring with glow */}
                <svg
                    className="absolute inset-0 w-full h-full -rotate-90 animate-spin drop-shadow-[0_0_8px_rgba(163,230,53,0.5)]"
                    viewBox="0 0 100 100"
                    style={{ animationDuration: '1.2s', animationTimingFunction: 'linear' }}
                >
                    <circle
                        cx="50" cy="50" r="46"
                        fill="none"
                        stroke="#a3e635"
                        strokeWidth="4"
                        strokeLinecap="round"
                        strokeDasharray="200"
                        strokeDashoffset="140"
                    />
                </svg>

                {/* Center AKPack Logo */}
                <div className="relative z-10 bg-[#0a1610] rounded-full p-2">
                    <svg viewBox="0 0 100 100" className="w-10 h-10" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M20 40 L50 20 L80 40 L80 80 L50 100 L20 80 Z" fill="#152219" stroke="#4d7c0f" strokeWidth="6" strokeLinejoin="round" />
                        <path d="M35 60 L65 60 M40 70 L60 70 M45 80 L55 80" stroke="#65a30d" strokeWidth="5" strokeLinecap="round" />
                        <path d="M50 20 C50 5, 35 0, 20 5 C25 20, 40 20, 50 20 Z" fill="#84cc16" />
                        <path d="M50 20 C50 5, 65 0, 80 5 C75 20, 60 20, 50 20 Z" fill="#a3e635" />
                        <path d="M50 20 L50 5" stroke="#a3e635" strokeWidth="4" strokeLinecap="round" />
                    </svg>
                </div>
            </div>
            <p className="text-xs font-bold text-[#a3e635] tracking-widest uppercase animate-pulse">{text}</p>
        </div>
    );
}