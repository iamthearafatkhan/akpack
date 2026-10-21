import { init as initZstd, decompress as zstdDecompress } from "@bokuweb/zstd-wasm";
// Import the raw module Promise directly (do not try to call it as a function)
import brotliPromise from 'brotli-dec-wasm';
import { unzlibSync } from "fflate";

const HEADER_SIZE = 64;

export async function decodeAkpInBrowser(
    file: File,
    onProgress: (pct: number) => void
): Promise<Blob> {
    // 1. Read Header
    const headerBuffer = await file.slice(0, HEADER_SIZE).arrayBuffer();
    const view = new DataView(headerBuffer);

    const magic = String.fromCharCode(view.getUint8(0), view.getUint8(1), view.getUint8(2), view.getUint8(3));
    if (magic !== "AKP1") throw new Error("Not a valid AKP file");

    const origSize = Number(view.getBigUint64(16, true));
    const manifestLen = Number(view.getBigUint64(24, true));

    // 2. Read Manifest
    const manifestStart = HEADER_SIZE;
    const manifestEnd = manifestStart + manifestLen;
    const manifestBuffer = await file.slice(manifestStart, manifestEnd).arrayBuffer();
    const manifestStr = new TextDecoder().decode(manifestBuffer);
    const manifest = JSON.parse(manifestStr);

    // 3. Initialize WASM Decoders concurrently
    // brotliPromise yields the fully ready instance once resolved
    const [, brotli] = await Promise.all([
        initZstd(),
        brotliPromise
    ]);

    const chunks = manifest.chunks;
    const decompressedChunks: Uint8Array[] = [];
    let payloadOffset = manifestEnd;
    let processedBytes = 0;

    // 4. Decompress chunks
    for (let i = 0; i < chunks.length; i++) {
        const meta = chunks[i];

        const payloadBuffer = await file.slice(payloadOffset, payloadOffset + meta.stored_len).arrayBuffer();
        payloadOffset += meta.stored_len;

        const payload = new Uint8Array(payloadBuffer);
        let decompressed: Uint8Array;

        if (meta.codec === 0) {
            decompressed = payload;
        } else if (meta.codec === 1) {
            decompressed = zstdDecompress(payload, meta.orig_len);
        } else if (meta.codec === 2) {
            // Use the initialized decompress method from the resolved module instance
            decompressed = brotli.decompress(payload);
        } else if (meta.codec === 3) {
            decompressed = unzlibSync(payload);
        } else {
            throw new Error(`Unsupported codec ID: ${meta.codec}`);
        }

        decompressedChunks.push(decompressed);

        processedBytes += meta.orig_len;
        onProgress(Math.round((processedBytes / origSize) * 100));
    }

    // 5. Combine into a single Blob
    return new Blob(decompressedChunks as any[], { type: "video/mp4" });
}
