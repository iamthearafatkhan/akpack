export function convertSrtToVtt(srtText: string): string {
    // Add the WEBVTT header
    let vtt = "WEBVTT\n\n";

    // Convert SRT timestamps (00:00:01,000) to VTT timestamps (00:00:01.000)
    const converted = srtText
        .replace(/\r\n|\r/g, '\n')
        .replace(/(\d{2}:\d{2}:\d{2}),(\d{3})/g, '$1.$2');

    return vtt + converted;
}