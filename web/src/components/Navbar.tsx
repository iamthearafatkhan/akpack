import { Link, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import Logo from "./Logo";

export default function Navbar() {
    const location = useLocation();
    const [isDark, setIsDark] = useState(true);

    useEffect(() => {
        // Check local storage or system preference on load
        const isDarkTheme = localStorage.getItem("theme") === "dark" ||
            (!("theme" in localStorage) && window.matchMedia("(prefers-color-scheme: dark)").matches);
        setIsDark(isDarkTheme);
        if (isDarkTheme) document.documentElement.classList.add("dark");
    }, []);

    const toggleTheme = () => {
        const newDark = !isDark;
        setIsDark(newDark);
        if (newDark) {
            document.documentElement.classList.add("dark");
            localStorage.setItem("theme", "dark");
        } else {
            document.documentElement.classList.remove("dark");
            localStorage.setItem("theme", "light");
        }
    };

    return (
        <nav className="border-b border-gray-200 dark:border-[#2d4a37] bg-white/90 dark:bg-[#0a1610]/90 backdrop-blur-md sticky top-0 z-50 transition-colors">
            <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
                <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                    <Logo className="w-8 h-8" />
                    <span className="font-bold text-xl text-[#4d7c0f] dark:text-[#a3e635] tracking-tight">AKPack</span>
                </Link>

                <div className="flex items-center gap-6 text-sm font-medium text-gray-600 dark:text-[#8fa896]">
                    <div className="flex gap-6">
                        <Link to="/" className={`hover:text-[#4d7c0f] dark:hover:text-[#a3e635] transition-colors ${location.pathname === "/" ? "text-[#4d7c0f] dark:text-[#a3e635]" : ""}`}>Home</Link>
                        <Link to="/faq" className={`hover:text-[#4d7c0f] dark:hover:text-[#a3e635] transition-colors ${location.pathname === "/faq" ? "text-[#4d7c0f] dark:text-[#a3e635]" : ""}`}>FAQ</Link>
                        <Link to="/privacy" className={`hover:text-[#4d7c0f] dark:hover:text-[#a3e635] transition-colors ${location.pathname === "/privacy" ? "text-[#4d7c0f] dark:text-[#a3e635]" : ""}`}>Privacy</Link>
                    </div>

                    {/* Theme Toggle Button */}
                    <button onClick={toggleTheme} className="p-2 rounded-lg bg-gray-100 dark:bg-[#152219] hover:bg-gray-200 dark:hover:bg-[#2d4a37] transition-colors" aria-label="Toggle Theme">
                        {isDark ? "☀️" : "🌙"}
                    </button>
                </div>
            </div>
        </nav>
    );
}