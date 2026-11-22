# /// script
# requires-python = ">=3.10"
# dependencies = ["imageio-ffmpeg>=0.5"]
# ///
"""Stage 5: render <project>/plan.json into the final video with ffmpeg.

Still images get a camera move (zoom/pan), video clips are trimmed and cropped to the frame,
transparent overlays (captions, titles) are composited on top, audio tracks are mixed, and any
track marked "voice" ducks the others while it plays.

usage: uv run assemble.py <project> [--plan other.json] [--show-command]
"""
import argparse, json, shutil, subprocess, sys
from pathlib import Path

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def ffmpeg_exe():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def camera_move(kind, n, W, H, fps):
    """zoompan filter that turns one still image into n frames of motion."""
    z = {"zoom_in": f"1+0.15*on/{n}", "zoom_out": f"1.15-0.15*on/{n}"}.get(kind, "1.12")
    x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    if kind == "pan_left":
        x = f"(iw-iw/zoom)*(1-on/{n})"
    elif kind == "pan_right":
        x = f"(iw-iw/zoom)*on/{n}"
    elif kind == "none":
        z = "1"
    # upscale 2x before zoompan so the move does not jitter
    return (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
            f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={fps}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--plan", default="plan.json")
    ap.add_argument("--show-command", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        print("assemble.py: ok; ffmpeg =", ffmpeg_exe()); return

    P = Path(a.project).expanduser().resolve()
    plan = json.loads((P / a.plan).read_text())
    W, H, fps = int(plan.get("width", 1080)), int(plan.get("height", 1920)), int(plan.get("fps", 30))
    output = P / plan.get("output", "04_render/final.mp4")
    output.parent.mkdir(parents=True, exist_ok=True)

    def path(p):
        q = Path(p).expanduser()
        q = q if q.is_absolute() else P / q
        if not q.exists():
            sys.exit(f"file in plan does not exist: {q}")
        return str(q)

    args, filters, labels = [], [], []
    idx, total = 0, 0.0
    for k, c in enumerate(plan["clips"]):
        src = path(c["file"]); dur = float(c["duration"]); n = max(1, round(dur * fps))
        if Path(src).suffix.lower() in IMAGE_EXT:
            args += ["-i", src]
            f = f"[{idx}:v]{camera_move(c.get('move', 'zoom_in'), n, W, H, fps)}"
        else:
            args += ["-ss", str(c.get("start", 0)), "-t", f"{dur + 0.5:.3f}", "-i", src]
            f = f"[{idx}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={fps}"
        f += f",trim=end_frame={n},setpts=PTS-STARTPTS,setsar=1,format=yuv420p[v{k}]"
        filters.append(f); labels.append(f"[v{k}]"); idx += 1; total += n / fps
    filters.append(f"{''.join(labels)}concat=n={len(labels)}:v=1:a=0[base0]")

    # overlays: transparent layers (e.g. Remotion captions/titles as ProRes 4444 .mov) on top of the edit
    base = "base0"
    for k, ov in enumerate(plan.get("overlays", [])):
        args += ["-i", path(ov["file"])]
        at = float(ov.get("at", 0))
        filters.append(f"[{idx}:v]scale={W}:{H},fps={fps},format=yuva420p,setpts=PTS-STARTPTS+{at}/TB[ov{k}]")
        filters.append(f"[{base}][ov{k}]overlay=eof_action=pass:format=auto[base{k + 1}]")
        base = f"base{k + 1}"; idx += 1
    filters.append(f"[{base}]format=yuv420p[vout]")

    music, voices = [], []
    for t, track in enumerate(plan.get("audio", [])):
        args += ["-i", path(track["file"])]
        ms = int(float(track.get("at", 0)) * 1000)
        skip = float(track.get("skip", 0))
        filters.append(f"[{idx}:a]aresample=44100,aformat=channel_layouts=stereo,atrim=start={skip},asetpts=PTS-STARTPTS,"
                       f"adelay={ms}|{ms},volume={track.get('volume', 1.0)},apad,atrim=end={total:.3f}[a{t}]")
        (voices if track.get("voice") else music).append(f"[a{t}]"); idx += 1

    def mix(lst, name):
        if len(lst) == 1:
            filters.append(f"{lst[0]}anull[{name}]")
        else:
            filters.append(f"{''.join(lst)}amix=inputs={len(lst)}:normalize=0:duration=longest[{name}]")

    fade = float(plan.get("audio_fade", 0.3))
    audio_map = []
    if music or voices:
        if music and voices:
            mix(music, "mus"); mix(voices, "vox")
            filters.append("[vox]asplit=2[vox1][voxsc]")
            filters.append("[mus][voxsc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=300[duck]")
            filters.append("[duck][vox1]amix=inputs=2:normalize=0:duration=longest[amix]")
        else:
            mix(music or voices, "amix")
        filters.append(f"[amix]afade=t=in:d={fade},afade=t=out:st={max(total - fade, 0):.3f}:d={fade},alimiter=limit=0.95[aout]")
        audio_map = ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"]

    cmd = [ffmpeg_exe(), "-y", "-v", "error", "-stats", *args, "-filter_complex", ";".join(filters),
           "-map", "[vout]", *audio_map, "-c:v", "libx264", "-crf", "18", "-preset", "medium",
           "-pix_fmt", "yuv420p", "-r", str(fps), "-t", f"{total:.3f}", "-movflags", "+faststart", str(output)]
    if a.show_command:
        print(" ".join(f"'{x}'" if " " in x or ";" in x else x for x in cmd))
    print(f"→ assembling {len(plan['clips'])} clips, {total:.2f}s, {W}x{H}@{fps}")
    if subprocess.run(cmd).returncode != 0:
        sys.exit("ffmpeg failed (run with --show-command to see the filter graph)")
    print(f"ok → {output}")


if __name__ == "__main__":
    main()
