import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
    plugins: [react()],
    server: {
        proxy: {
            "/api": "http://localhost:8000",
        },
    },
    optimizeDeps: {
        exclude: ["@bokuweb/zstd-wasm"],
    },
    esbuild: {
        target: "es2020",
    },
});