// Optional Remotion layer: animated captions and titles rendered as transparent overlays.
// Remotion is under the Remotion License: free for individuals and companies of up to 3 people,
// paid for larger companies (https://www.remotion.dev/docs/license/pricing). Set REMOTION_LICENSE_KEY
// if you have one, or "free-license" if you qualify for the free license.
//
// usage:
//   node remotion.mjs captions <project> [--transcript file] [--offset 0] [--words-per-page 1200] [--out file]
//   node remotion.mjs title <project> --title "Text" [--subtitle "Text"] [--dur 2] [--transparent] [--out file]
//   node remotion.mjs studio            (opens Remotion Studio to tweak the look)
// Size, fps and (for captions) length come from <project>/plan.json, so overlays always match the edit.
import { existsSync, mkdirSync, readFileSync, writeFileSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const RM = resolve(dirname(fileURLToPath(import.meta.url)), "..", "remotion");
const [, , cmd, projectArg, ...rest] = process.argv;
const opt = (k, d) => { const i = rest.indexOf(`--${k}`); return i >= 0 ? rest[i + 1] : d; };
const flag = (k) => rest.includes(`--${k}`);
const die = (m) => { console.error(m); process.exit(1); };

if (!existsSync(join(RM, "node_modules", "remotion")))
  die(`Remotion is not installed. Run: bash ${resolve(RM, "..", "scripts", "setup.sh")} --remotion`);

if (cmd === "studio") {
  spawnSync("npx", ["remotion", "studio", "src/index.ts"], { cwd: RM, stdio: "inherit" });
  process.exit(0);
}
if (!["captions", "title"].includes(cmd) || !projectArg) die("usage: node remotion.mjs captions|title|studio <project> [options]");

const P = resolve(projectArg);
const planPath = join(P, "plan.json");
const plan = existsSync(planPath) ? JSON.parse(readFileSync(planPath, "utf8")) : {};
const frame = { width: plan.width ?? 1080, height: plan.height ?? 1920, fps: plan.fps ?? 30 };
const editLength = (plan.clips ?? []).reduce((s, c) => s + Number(c.duration), 0);

let id, props, out;
if (cmd === "captions") {
  // Prefer the transcript of the finished edit (analyze.py --video 04_render/final.mp4), then the reference.
  const candidates = [opt("transcript"), join(P, "02_analysis/check_final/transcript.json"), join(P, "02_analysis/transcript.json")];
  const tPath = candidates.find((p) => p && existsSync(resolve(P, p)));
  if (!tPath) die("no transcript.json found: run analyze.py with transcription first");
  const offsetMs = Number(opt("offset", 0)) * 1000;
  const captions = [];
  for (const seg of JSON.parse(readFileSync(resolve(P, tPath), "utf8")).segments) {
    const words = seg.words?.length ? seg.words : [{ w: seg.text, s: seg.start, e: seg.end }];
    for (const w of words) {
      // @remotion/captions splits on the space before each word
      captions.push({ text: (captions.length ? " " : "") + w.w, startMs: w.s * 1000 + offsetMs, endMs: w.e * 1000 + offsetMs, timestampMs: null, confidence: null });
    }
  }
  const lastMs = captions.length ? captions[captions.length - 1].endMs : 1000;
  id = "Captions";
  props = { ...frame, durationInSeconds: editLength || lastMs / 1000 + 0.5, captions, wordsPerPageMs: Number(opt("words-per-page", 1200)) };
  out = opt("out", "03_assets/captions/captions.mov");
  console.log(`→ ${captions.length} words from ${tPath}`);
} else {
  id = "Title";
  props = { ...frame, durationInSeconds: Number(opt("dur", 2)), title: opt("title", "TITLE"), subtitle: opt("subtitle", ""), background: flag("transparent") ? "transparent" : "#0d0d10" };
  out = opt("out", flag("transparent") ? "03_assets/motion/title.mov" : "03_assets/motion/title.mp4");
}

const outPath = resolve(P, out);
mkdirSync(dirname(outPath), { recursive: true });
const tmp = mkdtempSync(join(tmpdir(), "remotion-props-"));
const propsFile = join(tmp, "props.json");
writeFileSync(propsFile, JSON.stringify(props));

const alpha = outPath.endsWith(".mov");
const args = ["remotion", "render", "src/index.ts", id, outPath, `--props=${propsFile}`, "--log=error"];
if (alpha) args.push("--codec=prores", "--prores-profile=4444", "--image-format=png", "--pixel-format=yuva444p10le");
const key = process.env.REMOTION_LICENSE_KEY;
if (key) args.push(`--license-key=${key}`);

console.log(`→ rendering ${id} ${props.width}x${props.height}@${props.fps}, ${props.durationInSeconds.toFixed(2)}s${alpha ? " (transparent)" : ""}`);
const r = spawnSync("npx", args, { cwd: RM, stdio: "inherit" });
rmSync(tmp, { recursive: true, force: true });
if (r.status !== 0) die("remotion render failed");
console.log(`ok → ${outPath}`);
