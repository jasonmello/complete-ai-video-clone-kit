#!/bin/bash
# Installs everything that can be installed without sudo. Downloads a few hundred MB.
# usage: setup.sh [--remotion]   (--remotion adds the optional Remotion layer; see its license in the README)
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
command -v uv >/dev/null || { echo "Install uv first: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }

# yt-dlp needs Python >= 3.10; on an older system Python uv would pin a stale release YouTube rejects.
echo "→ yt-dlp"; uv tool install --upgrade --python 3.12 "yt-dlp[default]"

echo "→ Python dependencies for analyze/assemble (uv cache)"
uv run "$DIR/analyze.py" --check
uv run "$DIR/assemble.py" --check

if ! command -v ffmpeg >/dev/null; then
  echo "→ ffmpeg on PATH (copy of the imageio-ffmpeg binary into ~/.local/bin)"
  FF=$(uv run --quiet "$DIR/assemble.py" --check | sed 's/.*ffmpeg = //')
  mkdir -p ~/.local/bin && cp "$FF" ~/.local/bin/ffmpeg && chmod +x ~/.local/bin/ffmpeg
fi

echo "→ puppeteer"
cd "$DIR"
if [ -d "/Applications/Google Chrome.app" ] || [ -n "$CHROME_PATH" ]; then npm install --no-fund --no-audit puppeteer-core@24
else npm install --no-fund --no-audit puppeteer@24; fi

if [ "${1:-}" = "--remotion" ]; then
  echo "→ Remotion (optional layer: animated captions and titles)"
  (cd "$DIR/../remotion" && npm install --no-fund --no-audit && npx remotion browser ensure)
fi

echo "Done. Demucs and the Whisper model download on first use. Blender: blender.org."
