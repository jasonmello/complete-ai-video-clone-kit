# AGENTS.md

**What it is:** a Claude Code skill (also a plugin) that orchestrates ten free AI video tools into a 5-stage pipeline that remakes a reference video's editing structure with the user's own material.

## Where things are
| Path | What |
|---|---|
| `skills/complete-ai-video-clone-kit/SKILL.md` | The skill Claude loads: stages, file contract, `plan.json` format, rules |
| `skills/complete-ai-video-clone-kit/scripts/` | `doctor.sh`, `setup.sh`, `download.sh`, `analyze.py`, `separate.sh`, `motion.mjs`, `motion_example.html`, `blender_turntable.py`, `assemble.py`, `remotion.mjs` |
| `skills/complete-ai-video-clone-kit/remotion/` | Optional Remotion project: `Captions` and `Title` compositions (own code; Remotion License applies to the packages) |
| `README.md` | User docs, English then Portuguese: 360° diagram, tool table, step by step, what was tested |
| `tests/` | `smoke.sh` (assemble + analyze on synthetic media), `check_docs.py` |
| `.claude-plugin/` | Plugin and marketplace manifests |
| `docs/decisions.md` | Decisions with date and reason |

## Commands
```bash
bash tests/smoke.sh          # end-to-end check, needs uv
(cd skills/complete-ai-video-clone-kit/remotion && npx tsc --noEmit)  # Remotion typecheck
python3 tests/check_docs.py  # docs cite only existing paths
```

## Rules that don't break
- The kit copies **structure, never content**. Footage, music or voices without rights or consent never go into a render. Voice cloning is for the user's own voice only.
- Python scripts declare dependencies inline (PEP 723) and run with `uv run`. No requirements.txt, no system Python.
- Stage file names are a contract (`01_reference/ref.mp4`, `02_analysis/map.json`, `plan.json`, `04_render/final.mp4`). Renaming one means updating `SKILL.md`, the README (both languages), and `tests/smoke.sh` in the same PR.
- Remotion stays **optional**. FFmpeg remains the assembler, and the kit must work without Remotion installed. Don't copy Remotion-licensed code (e.g. their Elements) into the repo.
- Docs: English first, then pt-BR. Update the README "What was tested" section whenever verification changes.

## Not verified
Blender template, larger Whisper models, Windows.

## Before X, read Y
| Before | Read |
|---|---|
| Changing a stage, a script option or `plan.json` | `SKILL.md` |
| Touching README, docs or the motion template look | `DESIGN.md` |
| Revisiting a tooling choice (uv, imageio-ffmpeg, pins) | `docs/decisions.md` |
| Commits, PRs, CI | the user's `fluxo-github` skill |
