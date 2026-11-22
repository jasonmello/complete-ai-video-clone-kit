"""Fails if a doc cites a repository path or script that no longer exists.

Checks markdown links and <img> sources pointing to local files and backticked script names (e.g. `assemble.py`)
in every tracked .md file. Run: python3 tests/check_docs.py
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "complete-ai-video-clone-kit" / "scripts"
# file names the docs talk about that are created at run time, not shipped
RUNTIME = {"ref.mp4", "final.mp4", "audio.wav", "map.json", "beats.json", "transcript.json",
           "subtitles.srt", "plan.json", "prompts.md", "page.html", "model.glb", "music.mp3"}

errors = []
for md in ROOT.rglob("*.md"):
    if any(p in md.parts for p in ("node_modules", "_out", ".git")):
        continue
    text = md.read_text(encoding="utf-8")
    links = re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", text) + re.findall(r'<img[^>]+src="([^"]+)"', text)
    for target in links:
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        if not (md.parent / target).exists():
            errors.append(f"{md.relative_to(ROOT)}: broken link → {target}")
    for name in set(re.findall(r"`(?:\$S/)?([\w.-]+\.(?:py|sh|mjs|html))\b", text)):
        if name in RUNTIME:
            continue
        if not ((SCRIPTS / name).exists() or list(ROOT.rglob(name))):
            errors.append(f"{md.relative_to(ROOT)}: cites missing script `{name}`")

if errors:
    print("\n".join(errors)); sys.exit(1)
print("docs ok")
