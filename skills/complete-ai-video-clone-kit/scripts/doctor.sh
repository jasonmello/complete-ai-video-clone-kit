#!/bin/bash
# Shows which parts of the kit are ready on this machine. Read-only.
DIR="$(cd "$(dirname "$0")" && pwd)"
ok(){ printf "  ✅ %-12s %s\n" "$1" "$2"; }
no(){ printf "  ❌ %-12s %s\n" "$1" "$2"; }
info(){ printf "  ⓘ  %s\n" "$1"; }

echo "Complete AI Video Clone Kit: doctor"
command -v uv >/dev/null && ok uv "$(uv --version)" || no uv "required: curl -LsSf https://astral.sh/uv/install.sh | sh"
command -v node >/dev/null && ok node "$(node --version)" || no node "needed for motion (Puppeteer) and as yt-dlp's JS runtime"
command -v yt-dlp >/dev/null && ok yt-dlp "$(yt-dlp --version)" || no yt-dlp "setup.sh installs it (or download.sh runs it through uvx)"
command -v ffmpeg >/dev/null && ok ffmpeg "$(command -v ffmpeg)" || no ffmpeg "not on PATH; setup.sh copies the bundled one to ~/.local/bin"
info "pyscenedetect, librosa, whisper: installed by uv on the first 'uv run analyze.py'"
info "demucs: fetched by uvx on the first 'separate.sh' (~1 GB of PyTorch)"
if command -v blender >/dev/null; then ok blender "$(command -v blender)"
elif [ -x /Applications/Blender.app/Contents/MacOS/Blender ]; then ok blender "/Applications/Blender.app (not on PATH)"
else no blender "optional, only for 3D: blender.org"; fi
if [ -d "$DIR/node_modules/puppeteer-core" ] || [ -d "$DIR/node_modules/puppeteer" ]; then ok puppeteer "installed"
else no puppeteer "setup.sh runs npm install in scripts/"; fi
info "Google Flow and the voice-cloning tool are external services: nothing to install"
