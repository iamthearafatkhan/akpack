import Logo from "./Logo";

export default function Loader({ text }: { text: string }) {
    return (
        <div className="flex flex-col items-center justify-center py-8 space-y-4">
            <div className="relative">
                {/* Pulsing rings */}
                <div className="absolute inset-0 bg-[#84cc16] rounded-full animate-ping opacity-20"></div>
                <div className="relative bg-[#0a1610] p-2 rounded-full border border-[#4d7c0f]">
                    <Logo className="w-10 h-10 animate-bounce" />
                </div>
            </div>
            <p className="text-sm font-medium text-[#a3e635] tracking-widest uppercase animate-pulse">{text}</p>
        </div>
    );
}