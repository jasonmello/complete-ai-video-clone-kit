#!/bin/bash
# End-to-end smoke test with synthetic media: assemble a 4-clip edit cut on a 120 BPM beat,
# then analyze the result and assert the cuts and the beat were found.
# Skips download (network), Whisper and Demucs (large downloads), Blender and Puppeteer.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
S="$ROOT/skills/complete-ai-video-clone-kit/scripts"
T="$ROOT/tests/_out"
rm -rf "$T"; mkdir -p "$T"/{01_reference,03_assets/{images,voice}}

FF=$(command -v ffmpeg || uv run --quiet "$S/assemble.py" --check | sed 's/.*ffmpeg = //')
for i in 1 2 3; do
  c=$(echo red green blue | cut -d' ' -f$i)
  "$FF" -v error -f lavfi -i "testsrc2=s=1600x900,drawbox=c=$c@0.6:t=fill" -frames:v 1 "$T/03_assets/images/shot_0$i.png"
done
"$FF" -v error -f lavfi -i "testsrc=s=1280x720:r=30:d=6" -c:v libx264 -pix_fmt yuv420p "$T/01_reference/ref.mp4"
# click every 0.5 s (120 BPM) over a low drone
"$FF" -v error -f lavfi -i "aevalsrc='0.8*sin(2*PI*60*t)*exp(-30*mod(t,0.5))+0.2*sin(2*PI*110*t)':d=8:s=44100" "$T/music.wav"
"$FF" -v error -f lavfi -i "sine=f=800:d=2" "$T/03_assets/voice/narration.wav"
# transparent overlay with a white bar at the bottom, like a caption layer
# (drawbox keeps alpha at 0, so build an opaque bar and pad it with transparent pixels)
"$FF" -v error -f lavfi -i "color=c=white:s=540x80:d=5,format=rgba,pad=540:960:0:880:color=black@0.0" \
  -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le "$T/03_assets/overlay.mov"

cat > "$T/plan.json" <<'EOF'
{"output": "04_render/final.mp4", "width": 540, "height": 960, "fps": 30,
 "clips": [
  {"file": "03_assets/images/shot_01.png", "duration": 1.0, "move": "zoom_in"},
  {"file": "01_reference/ref.mp4", "start": 2.0, "duration": 1.5},
  {"file": "03_assets/images/shot_02.png", "duration": 1.0, "move": "pan_right"},
  {"file": "03_assets/images/shot_03.png", "duration": 1.5, "move": "zoom_out"}],
 "audio": [{"file": "music.wav", "volume": 0.8},
           {"file": "03_assets/voice/narration.wav", "at": 1.0, "voice": true}],
 "overlays": [{"file": "03_assets/overlay.mov", "at": 0}],
 "audio_fade": 0.3}
EOF

uv run --quiet "$S/assemble.py" "$T"
# the overlay bar must show up white on top of the edit
bar=$("$FF" -v error -ss 2 -i "$T/04_render/final.mp4" -frames:v 1 -vf "crop=540:60:0:890,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-" -f null - 2>/dev/null | sed -n 's/.*YAVG=\([0-9.]*\).*/\1/p' | head -1)
python3 -c "import sys; y=float('$bar'); assert y > 200, f'overlay not visible (YAVG {y})'; print(f'overlay ok (YAVG {y:.0f})')"
uv run --quiet "$S/analyze.py" "$T" --video 04_render/final.mp4 --no-transcript 2>/dev/null

python3 - "$T/02_analysis/check_final/map.json" <<'EOF'
import json, sys
m = json.load(open(sys.argv[1])); s = m["summary"]
starts = [p["start"] for p in m["shots"]]
assert s["shots"] == 4, f"expected 4 shots, got {s['shots']}: {starts}"
for want, got in zip([0.0, 1.0, 2.5, 3.5], starts):
    assert abs(want - got) < 0.05, f"cut at {got}, expected {want}"
assert 110 <= s["bpm"] <= 130, f"bpm {s['bpm']} not near 120"
assert s["cuts_on_beat_pct"] >= 66, f"only {s['cuts_on_beat_pct']}% of cuts on the beat"
print(f"smoke ok: {s['shots']} shots, {s['bpm']} BPM, {s['cuts_on_beat_pct']}% on the beat")
EOF
