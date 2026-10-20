export default function Logo({ className = "w-8 h-8", animated = false }: { className?: string, animated?: boolean }) {
    return (
        <svg
            viewBox="0 0 100 100"
            className={`${className} ${animated ? "animate-pulse" : ""}`}
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
        >
            {/* Compressed Box (The Pack) */}
            <path d="M20 40 L50 20 L80 40 L80 80 L50 100 L20 80 Z" fill="#152219" stroke="#4d7c0f" strokeWidth="6" strokeLinejoin="round" />

            {/* Inner Compression lines (The Zstd / Data) */}
            <path d="M35 60 L65 60 M40 70 L60 70 M45 80 L55 80" stroke="#65a30d" strokeWidth="5" strokeLinecap="round" />

            {/* Leaves sprouting (The Forest / Life) */}
            <path d="M50 20 C50 5, 35 0, 20 5 C25 20, 40 20, 50 20 Z" fill="#84cc16" />
            <path d="M50 20 C50 5, 65 0, 80 5 C75 20, 60 20, 50 20 Z" fill="#a3e635" />

            {/* Center Stem */}
            <path d="M50 20 L50 5" stroke="#a3e635" strokeWidth="4" strokeLinecap="round" />
        </svg>
    );
}