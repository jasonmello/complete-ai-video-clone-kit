#!/bin/bash
# Stage 2b: split voice from music with Demucs (htdemucs, two stems).
# usage: separate.sh <project> [file]  →  <project>/02_analysis/stems/{vocals,no_vocals}.wav
# Default input is 02_analysis/audio.wav, written by analyze.py.
set -e
P="${1:-.}"; IN="${2:-$P/02_analysis/audio.wav}"
[ -f "$IN" ] || { echo "$IN not found. Run analyze.py first or pass a file."; exit 1; }
TMP="$P/02_analysis/_demucs"; mkdir -p "$TMP" "$P/02_analysis/stems"
# torchaudio >= 2.9 needs torchcodec to save files; pinning below it avoids that known error.
uvx --python 3.11 --with "torch<2.9" --with "torchaudio<2.9" --with soundfile \
  demucs --two-stems=vocals -n htdemucs -o "$TMP" "$IN"
NAME="$(basename "${IN%.*}")"
mv "$TMP/htdemucs/$NAME/vocals.wav" "$TMP/htdemucs/$NAME/no_vocals.wav" "$P/02_analysis/stems/"
rm -rf "$TMP"
ls -1 "$P/02_analysis/stems/"
