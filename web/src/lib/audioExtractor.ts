// web/src/lib/audioExtractor.ts
export async function extractAudioChunks(videoBlob: Blob, chunkMinutes: number = 5): Promise<Blob[]> {
    const arrayBuffer = await videoBlob.arrayBuffer();
    const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
    const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);

    const sampleRate = audioBuffer.sampleRate;
    const totalSamples = audioBuffer.length;
    const chunkSamples = chunkMinutes * 60 * sampleRate;
    const numChunks = Math.ceil(totalSamples / chunkSamples);
    const chunks: Blob[] = [];

    const channelData = audioBuffer.getChannelData(0);

    for (let i = 0; i < numChunks; i++) {
        const start = i * chunkSamples;
        const end = Math.min(start + chunkSamples, totalSamples);
        const length = end - start;

        const buffer = new ArrayBuffer(44 + length * 2);
        const view = new DataView(buffer);

        const writeString = (view: DataView, offset: number, string: string) => {
            for (let i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i));
            }
        };

        writeString(view, 0, 'RIFF');
        view.setUint32(4, 36 + length * 2, true);
        writeString(view, 8, 'WAVE');
        writeString(view, 12, 'fmt ');
        view.setUint32(16, 16, true);
        view.setUint16(20, 1, true);
        view.setUint16(22, 1, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, sampleRate * 2, true);
        view.setUint16(32, 2, true);
        view.setUint16(34, 16, true);
        writeString(view, 36, 'data');
        view.setUint32(40, length * 2, true);

        let offset = 44;
        for (let j = start; j < end; j++) {
            const sample = Math.max(-1, Math.min(1, channelData[j]));
            view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
            offset += 2;
        }

        chunks.push(new Blob([buffer], { type: "audio/wav" }));
    }

    return chunks;
}