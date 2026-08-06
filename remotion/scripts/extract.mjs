// Pull the slides out of the authored storyboard into JSON the composition can import.
//
// This is the same shape as the real pipeline: the render NEVER invents content, it reads
// what was authored. If a slide is not in the storyboard it does not appear in the video,
// and that is the point — the storyboard is the spec, and the render is checked against it.
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const kit = join(here, "..", "..");
const board = join(kit, "brands", "northgate-home", "content", "storyboards",
                   "spring-tuneup", "beat-01", "reel.md");

const raw = readFileSync(board, "utf-8");

// front matter -> the machine-readable half
const fm = {};
const fmBlock = raw.match(/^---\n([\s\S]*?)\n---/);
if (fmBlock) {
  for (const line of fmBlock[1].split("\n")) {
    const m = line.match(/^([a-z_]+):\s*"?([^"#]*)"?\s*(#.*)?$/);
    if (m) fm[m[1]] = m[2].trim();
  }
}

// "## Slides" -> one entry per line
const slides = [];
const sl = raw.split(/^## Slides\s*$/m)[1] ?? "";
for (const line of sl.split("\n")) {
  const m = line.match(/^-\s+(.*)$/);
  if (!m) continue;
  const text = m[1].trim();
  const onScreen = text.match(/On-screen:\s*"([^"]+)"/);
  slides.push({
    direction: text.replace(/\s*On-screen:\s*"[^"]+"\s*/, "").trim(),
    onScreen: onScreen ? onScreen[1] : null,
  });
}

if (!slides.length) {
  console.error("No slides found. The storyboard is the spec — without it there is nothing to render.");
  process.exit(1);
}

const out = {
  title: fm.title ?? "Untitled",
  fps: Number(fm.fps ?? 30),
  lengthFrames: Number(fm.length_frames ?? 900),
  pillar: fm.pillar ?? "",
  slides,
};
mkdirSync(join(here, "..", "src"), { recursive: true });
writeFileSync(join(here, "..", "src", "data.json"), JSON.stringify(out, null, 2));
console.log(`extracted ${slides.length} slides · ${out.lengthFrames} frames @ ${out.fps}fps`);
