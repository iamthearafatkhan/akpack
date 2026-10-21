export async function extractAudioChunks(videoBlob: Blob, chunkMinutes: number = 5): Promise<Blob[]> {
    // We will use MediaRecorder to extract audio as WebM (Opus)
    // This is much smaller and more compatible with Groq than raw WAV.

    const video = document.createElement("video");
    video.src = URL.createObjectURL(videoBlob);
    video.muted = true;

    // Wait for video metadata to load
    await new Promise((resolve) => { video.onloadedmetadata = resolve; });

    const audioContext = new AudioContext();
    const source = audioContext.createMediaElementSource(video);
    const destination = audioContext.createMediaStreamDestination();
    source.connect(destination);

    // We need to play the video silently to capture audio
    const mediaRecorder = new MediaRecorder(destination.stream, { mimeType: 'audio/webm' });
    const chunks: Blob[] = [];
    mediaRecorder.ondataavailable = (e) => chunks.push(e.data);

    return new Promise((resolve, reject) => {
        mediaRecorder.onstop = () => resolve([new Blob(chunks, { type: 'audio/webm' })]);
        mediaRecorder.onerror = (e) => reject(e);

        mediaRecorder.start();
        video.play();

        // Stop after chunkMinutes
        setTimeout(() => {
            mediaRecorder.stop();
            video.pause();
            resolve([new Blob(chunks, { type: 'audio/webm' })]);
        }, chunkMinutes * 60 * 1000);
    });
}