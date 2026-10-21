export async function extractAudioFromVideo(videoBlob: Blob): Promise<Blob> {
    const arrayBuffer = await videoBlob.arrayBuffer();
    // Create an AudioContext at 16kHz (Whisper requires 16kHz audio)
    const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });

    // Decode the video's audio track
    const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);

    // Convert to WAV format
    const numOfChan = 1; // Mono
    const length = audioBuffer.length * numOfChan * 2 + 44;
    const buffer = new ArrayBuffer(length);
    const view = new DataView(buffer);
    const channels = [];
    let i;
    let sample;
    let offset = 0;
    let pos = 0;

    // Write WAV Header
    function setUint16(data: number) { view.setUint16(pos, data, true); pos += 2; }
    function setUint32(data: number) { view.setUint32(pos, data, true); pos += 4; }

    setUint32(0x46464952);                         // "RIFF"
    setUint32(length - 8);                         // file length - 8
    setUint32(0x45564157);                         // "WAVE"
    setUint32(0x20746d66);                         // "fmt " chunk
    setUint32(16);                                 // length = 16
    setUint16(1);                                  // PCM (uncompressed)
    setUint16(numOfChan);
    setUint32(audioBuffer.sampleRate);
    setUint32(audioBuffer.sampleRate * 2 * numOfChan); // avg. bytes/sec
    setUint16(numOfChan * 2);                      // block-align
    setUint16(16);                                 // 16-bit
    setUint32(0x61746164);                         // "data" chunk
    setUint32(length - pos - 4);                   // chunk length

    // Write interleaved PCM data
    const channelData = audioBuffer.getChannelData(0);
    while (pos < length) {
        for (i = 0; i < numOfChan; i++) {
            sample = channelData[offset++];
            sample = Math.max(-1, Math.min(1, sample));
            sample = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
            view.setInt16(pos, sample, true);
            pos += 2;
        }
    }

    return new Blob([buffer], { type: "audio/wav" });
}