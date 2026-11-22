#!/bin/bash
# Stage 1: download the reference video.
# usage: download.sh "<url>" <project>  →  <project>/01_reference/ref.mp4
set -e
URL="$1"; P="${2:-.}"
[ -z "$URL" ] && { echo "usage: download.sh <url> <project>"; exit 1; }
mkdir -p "$P/01_reference"
if command -v yt-dlp >/dev/null; then Y=(yt-dlp); else Y=(uvx --python 3.12 yt-dlp); fi
# YouTube now needs a JS runtime; yt-dlp only enables deno by default, so fall back to node.
JS=(); command -v deno >/dev/null || { command -v node >/dev/null && JS=(--js-runtimes node); }
# prefer H.264: AV1 is not decoded by every OpenCV build or editor
"${Y[@]}" "${JS[@]}" -f "bv*[vcodec^=avc1]+ba[ext=m4a]/bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b" \
  --merge-output-format mp4 -o "$P/01_reference/ref.%(ext)s" --no-playlist "$URL"
echo "$P/01_reference/ref.mp4"
