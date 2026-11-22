# DESIGN.md

The kit has no app UI. What users see is the **docs**, the **terminal output** of the scripts, and the **videos** it renders. These rules come from the code as it is.

## Principles
1. **Structure, not content.** Every piece of copy says the kit clones editing (cuts, beat, pacing), never footage, music or voices.
2. **Show the contract.** Docs name the exact file each stage reads and writes, so users can resume at any stage.
3. **Say what was not tested.** Every release lists what was verified and what was not.

## Voice (README, SKILL.md, script messages)
- English first, then pt-BR with the same structure and substance. No machine-literal translation.
- Plain, direct sentences. Name tools by their real names (yt-dlp, PySceneDetect, librosa, Whisper, Demucs, Google Flow, Blender, Puppeteer, FFmpeg).
- Script progress lines start with `→` and end with `ok → <path>`. Errors say what is missing and how to fix it.
- `doctor.sh` uses ✅ (ready), ❌ (missing, with the fix) and ⓘ (installed on first use / external).

## Render defaults (`assemble.py`)
| Setting | Value |
|---|---|
| Frame | 1080×1920, 30 fps (overridable in `plan.json`) |
| Video | H.264, CRF 18, `yuv420p`, `+faststart` |
| Audio | AAC 192 kbps, 0.3 s fade in/out, limiter at 0.95 |
| Still-image move | 15% zoom in/out over the clip, or a pan; images are upscaled 2× first so the move doesn't jitter |
| Ducking | sidechain compressor, threshold 0.03, ratio 8, attack 20 ms, release 300 ms |

## Motion template (`motion_example.html`)
| Token | Value |
|---|---|
| Background | `#0d0d10` |
| Title | `#fff`, 11vw, letter-spacing −0.03em |
| Accent bar | `#ff4d2e`, 1.2vh tall, grows to 60vw |
| Subtitle | `#bbb`, 4.5vw |
| Font | `-apple-system, Helvetica, sans-serif` |
| Easing | ease-out cubic `1 − (1 − x)³` |
| Timing | title 0–0.5 s, bar from 0.35 s, subtitle from 0.6 s, each 0.5 s |

Motion pages must be deterministic: they draw from `window.seek(t)` alone, with no timers or `requestAnimationFrame`.

## Captions (`remotion/src/Captions.tsx`)
| Token | Value |
|---|---|
| Text | `#fff`, weight 800, 8.5% of frame width, line height 1.15 |
| Active word | `#ff4d2e` |
| Legibility | black stroke 0.6% of width, shadow `0 4px 18px rgba(0,0,0,.55)` |
| Position | centered, 86% of width, 22% from the bottom (clear of platform UI) |
| Motion | a page pops in from 90% scale with a short spring; words light up in time |

## Plugin icon (`.claude-plugin/icon.png`)
A 1024×1024 waveform on `#0d0d10`: white bars on the left, `#bbb` bars on the right, and one `#ff4d2e` cut line in the middle. It shows the kit's core idea, a cut landing on the beat.
