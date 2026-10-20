import { Link, useLocation } from "react-router-dom";
import Logo from "./Logo";

export default function Navbar() {
    const location = useLocation();

    return (
        <nav className="border-b border-[#2d4a37] bg-[#0a1610]/90 backdrop-blur-md sticky top-0 z-50 transition-colors">
            <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
                <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                    <Logo className="w-8 h-8" />
                    <span className="font-bold text-xl text-[#a3e635] tracking-tight">AKPack</span>
                </Link>

                <div className="flex items-center gap-6 text-sm font-medium text-[#8fa896]">
                    <Link to="/" className={`hover:text-[#a3e635] transition-colors ${location.pathname === "/" ? "text-[#a3e635]" : ""}`}>Home</Link>
                    <Link to="/faq" className={`hover:text-[#a3e635] transition-colors ${location.pathname === "/faq" ? "text-[#a3e635]" : ""}`}>FAQ</Link>
                    <Link to="/privacy" className={`hover:text-[#a3e635] transition-colors ${location.pathname === "/privacy" ? "text-[#a3e635]" : ""}`}>Privacy</Link>
                </div>
            </div>
        </nav>
    );
}