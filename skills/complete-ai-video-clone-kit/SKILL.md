---
name: complete-ai-video-clone-kit
description: Orchestrates a free AI video toolkit (yt-dlp, PySceneDetect, librosa, Whisper, Demucs, a voice-cloning tool, Google Flow, Blender, Puppeteer, FFmpeg) as one pipeline, from a reference video to a finished MP4. It copies a reference's structure (shot lengths, cuts on the beat, pacing, speech timing), never its content. Use when the user wants to remake the rhythm of a reference video with their own material, make a short (Reels, TikTok, Shorts) with AI images cut to the beat, find the cuts or the BPM of a video, split voice from music, transcribe and subtitle, render HTML motion graphics or a 3D turntable, or assemble everything with ffmpeg. Triggers: "clone this video's editing", "same rhythm as this reel", "cut to the beat", "find the cuts", "separate the vocals", "assemble the video", "recria esse vídeo", "corta na batida", "faz um reels igual a esse".
---

# Complete AI Video Clone Kit

Five stages. Each stage writes files with fixed names into one project folder, and the next stage reads them. Any stage can be re-run or resumed, and each tool only has to know its own piece.

```
1 REFERENCE  yt-dlp ───────────────────────────▶ 01_reference/ref.mp4
2 ANALYSIS   PySceneDetect + librosa + Whisper ─▶ 02_analysis/map.json (+ frames/, subtitles.srt)
             Demucs ───────────────────────────▶ 02_analysis/stems/{vocals,no_vocals}.wav
3 ASSETS     Google Flow · Blender · Puppeteer · voice ─▶ 03_assets/
4 PLAN       you (Claude) write plan.json from map.json
5 ASSEMBLY   FFmpeg (assemble.py) ─────────────▶ 04_render/final.mp4
```

`S=<this skill folder>/scripts`. Python scripts run with `uv run` and declare their own dependencies (PEP 723): uv fetches Python and the libraries on first use, so the system Python is never touched.

## Before starting
1. Run `bash $S/doctor.sh` and tell the user what is missing. To install, ask first, then run `bash $S/setup.sh` (several hundred MB).
2. Create the project: `mkdir -p <project>/{01_reference,02_analysis,03_assets/{images,3d,motion,voice},04_render}`.
3. Ask only what changes the result: aspect ratio (9:16, 16:9, 1:1), length, topic or product, and the audio source (licensed music, the user's own track, or narration).

## 1. Reference: yt-dlp
`bash $S/download.sh "<url>" <project>` saves to `01_reference/ref.mp4` (H.264 preferred). The reference is for studying rhythm and structure. Its footage and music do not go into the final video unless the user holds the rights. Many platforms' terms do not allow downloading. When the user doesn't own the video or have permission, ask for a file they do own (or an export from their own account) and place it at `01_reference/ref.mp4` instead of downloading.

## 2. Analysis
`uv run $S/analyze.py <project>` writes to `02_analysis/`:
- `map.json`: every shot (start, end, duration, nearest beat, offset in ms, speech in that shot) and a summary (BPM, seconds per shot, % of cuts on the beat, beats per shot).
- `frames/shot_XX.jpg`: the middle frame of each shot. **Read these frames** to understand what each shot shows.
- `beats.json`, `transcript.json` (word timestamps), `subtitles.srt`, `audio.wav`.

Options: `--no-transcript`, `--model small|medium|large-v3` (default `small`), `--lang en`, `--threshold 27` (lower it if cuts are missed).
Without music, the BPM is noise (librosa finds a "beat" in speech). In that case ignore `cuts_on_beat_pct`.

Voice/music split: `bash $S/separate.sh <project>` (Demucs). The first run downloads PyTorch (~1 GB) and runs on the CPU.

## 3. Assets
- **Images, Google Flow (labs.google/flow):** a web service with nothing to install. Write `03_assets/prompts.md` with one prompt per shot, based on that shot's frame and duration. Start every prompt with the same style line, so the images stay consistent, and give the aspect ratio. The user generates the images and saves them as `03_assets/images/shot_XX.png`. Never automate Flow (or any other Google service) with a browser bot: the user generates by hand, which keeps their account inside Google's terms.
- **3D, Blender:** `blender -b -P $S/blender_turntable.py -- model.glb 03_assets/3d/turntable 4 30 1080 1920` renders a 360° turn to transparent PNGs. For custom scenes, write another `bpy` script in the same style.
- **Motion, Remotion (optional, preferred when installed):** `node $S/remotion.mjs title <project> --title "Text" --subtitle "Text" --dur 2 [--transparent]` renders the title composition at the size and fps in `plan.json`. For custom motion, add a composition in `remotion/src/` (see the `remotion-best-practices` skill) and preview it with `node $S/remotion.mjs studio`. Check `doctor.sh`: if Remotion isn't installed, use Puppeteer.
- **Motion, Puppeteer (no extra install):** write an HTML page that exposes `window.seek(t)` (t in seconds) and draws that instant without timers. Then run `node $S/motion.mjs page.html 03_assets/motion/title.mp4 --dur 2 --fps 30 --w 1080 --h 1920`. Add `--alpha` for a transparent ProRes `.mov`. Starting point: `$S/motion_example.html`.
- **Cloned voice (any voice-cloning tool):** only the user's own voice, or a voice whose owner gave written consent. Never clone a real person's voice without consent. Save the result to `03_assets/voice/`.

## 3b. Captions on screen (optional, Remotion)
Word-by-word animated captions as a transparent layer. Captions must follow the *final* audio, so the order is:
1. Assemble once without overlays.
2. Transcribe the result: `uv run $S/analyze.py <project> --video 04_render/final.mp4`.
3. Run `node $S/remotion.mjs captions <project>`, which reads that transcript (or `--transcript file`) and writes `03_assets/captions/captions.mov`. Use `--words-per-page 1200` for more or fewer words per page and `--offset s` to shift the timing.
4. Add the file to `overlays` and assemble again (assembly is fast).

**Remotion license:** free for individuals and companies of up to 3 people. Larger companies need a paid license, even when an individual makes videos *for* that company. Ask the user before using Remotion on company work. If they have a key, set `REMOTION_LICENSE_KEY` (or `free-license` if they qualify).

## 4. Plan: `plan.json`
Write it from `map.json`: one clip per reference shot, with the shot's duration (or nudged onto the beat). Cuts that land on the beat are what make it feel edited.

```json
{
  "output": "04_render/final.mp4", "width": 1080, "height": 1920, "fps": 30,
  "clips": [
    {"file": "03_assets/images/shot_01.png", "duration": 1.25, "move": "zoom_in"},
    {"file": "03_assets/motion/title.mp4", "duration": 2.0},
    {"file": "03_assets/3d/turntable.mp4", "start": 0.5, "duration": 0.8}
  ],
  "audio": [
    {"file": "music.mp3", "volume": 0.8},
    {"file": "03_assets/voice/narration.wav", "at": 0.5, "volume": 1.0, "voice": true}
  ],
  "overlays": [
    {"file": "03_assets/captions/captions.mov", "at": 0}
  ],
  "audio_fade": 0.5
}
```
- `move` (images only) accepts `zoom_in`, `zoom_out`, `pan_left`, `pan_right` or `none`. `start` (videos) is the in-point in the source file.
- Overlays: transparent `.mov` layers (captions, titles) composited on top of the edit, in order. `at` is the start time.
- Audio: `at` places the track on the timeline and `skip` trims its beginning. Tracks with `"voice": true` duck the others while they play. Paths are relative to the project folder.

## 5. Assembly
`uv run $S/assemble.py <project>` renders `04_render/final.mp4` (H.264 + AAC). It uses the system ffmpeg, or the one bundled by `imageio-ffmpeg` if there is none.
To check the result, run `uv run $S/analyze.py <project> --video 04_render/final.mp4 --no-transcript` (written to `02_analysis/check_final/`, so the reference analysis is kept). Then compare `seconds_per_shot` and `cuts_on_beat_pct` with the reference.

## Rules
- Don't skip stages: when there is a reference, the plan comes from `map.json`, never from scratch.
- Third-party footage, music and voices never go into the final video without rights or consent. Warn the user when a plan uses any of them.
- Before the user publishes, remind them of two things. First, YouTube, TikTok and Instagram require a label on realistic AI-generated content and on synthetic voices. Second, unlicensed music triggers Content ID claims, muted audio or strikes.
- Verified state and known limits: see the repository README ("What was tested"). If a tool fails, read the error and adjust. Don't retry blindly.
