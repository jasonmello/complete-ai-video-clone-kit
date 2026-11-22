# /// script
# requires-python = ">=3.10,<3.13"
# dependencies = [
#   "scenedetect[opencv-headless]>=0.6.4",
#   "librosa>=0.10",
#   "faster-whisper>=1.0",
#   "imageio-ffmpeg>=0.5",
# ]
# ///
"""Stage 2: read a video's structure.

Cuts (PySceneDetect) + beats (librosa) + speech (faster-whisper) merged into one map.json.

usage: uv run analyze.py <project> [--video file] [--no-transcript] [--model small] [--lang en] [--threshold 27]
writes to <project>/02_analysis/: audio.wav, map.json, beats.json, transcript.json, subtitles.srt, frames/shot_XX.jpg
"""
import argparse, json, shutil, subprocess, sys
from pathlib import Path


def ffmpeg_exe():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"failed: {' '.join(map(str, cmd))}\n{r.stderr[-1500:]}")


def srt_time(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--video", help="analyze another video (e.g. your final render) instead of 01_reference/ref.mp4")
    ap.add_argument("--no-transcript", action="store_true")
    ap.add_argument("--model", default="small", help="whisper model: tiny, base, small, medium, large-v3")
    ap.add_argument("--lang", default=None, help="speech language (auto-detected if omitted)")
    ap.add_argument("--threshold", type=float, default=27.0, help="cut sensitivity; lower finds more cuts")
    ap.add_argument("--tolerance", type=float, default=0.08, help="seconds for a cut to count as 'on the beat'")
    ap.add_argument("--check", action="store_true", help="only import dependencies and exit")
    a = ap.parse_args()

    import numpy as np, librosa
    from scenedetect import detect, ContentDetector
    if a.check:
        import faster_whisper  # noqa: F401
        print("analyze.py: dependencies ok; ffmpeg =", ffmpeg_exe()); return

    P = Path(a.project).expanduser().resolve()
    video = Path(a.video).expanduser() if a.video else P / "01_reference" / "ref.mp4"
    if not video.is_absolute():
        video = video.resolve() if video.exists() else P / video
    if not video.exists():
        sys.exit(f"video not found: {video}")
    out = P / "02_analysis"
    if a.video:  # checking another video never overwrites the reference analysis
        out = out / f"check_{video.stem}"
    (out / "frames").mkdir(parents=True, exist_ok=True)
    ff = ffmpeg_exe()

    print("→ extracting audio")
    wav = out / "audio.wav"
    run([ff, "-y", "-v", "error", "-i", str(video), "-vn", "-ac", "2", "-ar", "44100", str(wav)])

    print("→ detecting cuts")
    scenes = detect(str(video), ContentDetector(threshold=a.threshold))
    sec = lambda tc: float(tc.seconds) if hasattr(type(tc), "seconds") else tc.get_seconds()
    shots = [(sec(s), sec(e)) for s, e in scenes]
    y, sr = librosa.load(str(wav), sr=22050, mono=True)
    dur = float(len(y) / sr)
    if not shots:
        shots = [(0.0, dur)]

    print("→ finding the beat")
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units="time")
    bpm = float(np.atleast_1d(tempo)[0])
    beats = [float(b) for b in beats]
    onsets = librosa.onset.onset_detect(y=y, sr=sr, units="time")
    (out / "beats.json").write_text(json.dumps(
        {"bpm": round(bpm, 2), "beats": [round(b, 3) for b in beats], "accents": [round(float(o), 3) for o in onsets]},
        indent=1))

    speech = []
    if not a.no_transcript:
        print(f"→ transcribing (whisper {a.model}; first run downloads the model)")
        from faster_whisper import WhisperModel
        model = WhisperModel(a.model, device="cpu", compute_type="int8")
        # hand over decoded audio: faster-whisper's own decoder breaks with recent PyAV releases
        y16, _ = librosa.load(str(wav), sr=16000, mono=True)
        segs, info = model.transcribe(y16.astype(np.float32), language=a.lang, vad_filter=True, word_timestamps=True)
        for s in segs:
            speech.append({"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip(),
                           "words": [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)} for w in (s.words or [])]})
        (out / "transcript.json").write_text(json.dumps({"language": info.language, "segments": speech}, ensure_ascii=False, indent=1))
        (out / "subtitles.srt").write_text("\n".join(
            f"{i}\n{srt_time(s['start'])} --> {srt_time(s['end'])}\n{s['text']}\n" for i, s in enumerate(speech, 1)), encoding="utf-8")

    print("→ building map and frames")
    arr = np.array(beats) if beats else np.array([0.0])
    items, on_beat = [], 0
    for i, (start, end) in enumerate(shots, 1):
        j = int(np.abs(arr - start).argmin()); offset = start - float(arr[j])
        if i > 1 and abs(offset) <= a.tolerance:
            on_beat += 1
        frame = out / "frames" / f"shot_{i:02}.jpg"
        run([ff, "-y", "-v", "error", "-ss", f"{(start + end) / 2:.3f}", "-i", str(video), "-frames:v", "1", "-vf", "scale=480:-2", str(frame)])
        items.append({
            "shot": i, "start": round(start, 3), "end": round(end, 3), "duration": round(end - start, 3),
            "nearest_beat": round(float(arr[j]), 3), "offset_ms": round(offset * 1000),
            "frame": str(frame.relative_to(P)),
            "speech": [s["text"] for s in speech if s["start"] < end and s["end"] > start],
        })
    cuts = max(len(shots) - 1, 0)
    summary = {
        "video": str(video), "duration_s": round(dur, 2), "shots": len(shots), "bpm": round(bpm, 1),
        "seconds_per_shot": round(dur / len(shots), 2),
        "cuts_on_beat_pct": round(100 * on_beat / cuts, 1) if cuts else None,
        "beats_per_shot": round((dur / len(shots)) / (60 / bpm), 2) if bpm else None,
        "has_speech": bool(speech),
    }
    (out / "map.json").write_text(json.dumps({"summary": summary, "shots": items}, ensure_ascii=False, indent=1))
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    print(f"ok → {out / 'map.json'}")


if __name__ == "__main__":
    main()
