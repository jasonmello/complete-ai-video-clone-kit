// Stage 3 (motion): render an HTML page frame by frame with Puppeteer, then encode with ffmpeg.
// The page must expose window.seek(t) (seconds, may be async) that draws the exact state at time t,
// with no timers or requestAnimationFrame, so every frame is deterministic.
// usage: node motion.mjs page.html out.mp4 [--dur 2] [--fps 30] [--w 1080] [--h 1920] [--alpha]
import { mkdtempSync, rmSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve, dirname } from "node:path";
import { spawnSync, execSync } from "node:child_process";
import { pathToFileURL, fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const here = dirname(fileURLToPath(import.meta.url));
const require = createRequire(join(here, "package.json"));
const [, , html, out, ...rest] = process.argv;
if (!html || !out) { console.error("usage: node motion.mjs page.html out.mp4 [--dur 2] [--fps 30] [--w 1080] [--h 1920] [--alpha]"); process.exit(1); }
const opt = (k, d) => { const i = rest.indexOf(`--${k}`); return i >= 0 ? Number(rest[i + 1]) : d; };
const dur = opt("dur", 2), fps = opt("fps", 30), W = opt("w", 1080), H = opt("h", 1920);
const alpha = rest.includes("--alpha");

let puppeteer, launchOpts = { headless: true, args: ["--force-device-scale-factor=1"] };
const chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
try { puppeteer = require("puppeteer"); }
catch { puppeteer = require("puppeteer-core"); launchOpts.executablePath = process.env.CHROME_PATH || chrome; }

function ffmpeg() {
  try { return execSync("command -v ffmpeg").toString().trim(); } catch {}
  return execSync(`uv run --quiet --with imageio-ffmpeg python -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"`).toString().trim();
}

const dir = mkdtempSync(join(tmpdir(), "motion-"));
const browser = await puppeteer.launch(launchOpts);
try {
  const page = await browser.newPage();
  await page.setViewport({ width: W, height: H, deviceScaleFactor: 1 });
  await page.goto(pathToFileURL(resolve(html)).href, { waitUntil: "networkidle0" });
  await page.evaluate(() => document.fonts && document.fonts.ready);
  if (!(await page.evaluate(() => typeof window.seek === "function"))) throw new Error("the page does not define window.seek(t)");
  const n = Math.round(dur * fps);
  for (let i = 0; i < n; i++) {
    await page.evaluate(async (t) => { await window.seek(t); }, i / fps);
    await page.screenshot({ path: join(dir, `f_${String(i).padStart(5, "0")}.png`), omitBackground: alpha });
    if (i % fps === 0) process.stdout.write(`\r${i}/${n} frames`);
  }
  console.log(`\r${n}/${n} frames`);
} finally { await browser.close(); }

const codec = alpha ? ["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le"]
                    : ["-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p"];
const target = alpha && out.endsWith(".mp4") ? out.replace(/\.mp4$/, ".mov") : out;
const r = spawnSync(ffmpeg(), ["-y", "-v", "error", "-framerate", String(fps), "-i", join(dir, "f_%05d.png"), ...codec, target], { stdio: "inherit" });
rmSync(dir, { recursive: true, force: true });
if (r.status !== 0) process.exit(1);
console.log(`ok → ${target}`);
