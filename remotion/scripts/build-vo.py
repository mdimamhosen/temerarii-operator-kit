"""Build voiceover WAV from the authored storyboard (data.json).

Automation rule: the render never invents copy. VO lines come from on-screen text
when present, otherwise the slide direction — same source Remotion reads.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src" / "data.json"
OUT = ROOT / "public" / "vo.wav"


def lines_from_storyboard() -> list[str]:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    lines: list[str] = []
    for slide in data.get("slides", []):
        text = (slide.get("onScreen") or slide.get("direction") or "").strip()
        if text:
            lines.append(text)
    if not lines:
        raise SystemExit("no VO lines — extract.mjs must run first")
    return lines


def speak_windows(lines: list[str], dest: Path) -> None:
    """Windows SAPI — no API key, scriptable, calm rate."""
    # Escape for PowerShell single-quoted strings
    def esc(s: str) -> str:
        return s.replace("'", "''")

    ps_lines = ",\n  ".join(f"'{esc(l)}'" for l in lines)
    script = f"""
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = -2
$synth.Volume = 85
try {{
  $prefer = $synth.GetInstalledVoices() |
    ForEach-Object {{ $_.VoiceInfo }} |
    Where-Object {{ $_.Name -match 'Zira|Jenny|Aria|Female' }} |
    Select-Object -First 1
  if ($prefer) {{ $synth.SelectVoice($prefer.Name) }}
}} catch {{}}
$out = '{esc(str(dest))}'
New-Item -ItemType Directory -Force -Path (Split-Path $out) | Out-Null
$synth.SetOutputToWaveFile($out)
$lines = @(
  {ps_lines}
)
foreach ($line in $lines) {{
  $synth.Speak($line)
  Start-Sleep -Milliseconds 300
}}
$synth.Dispose()
Write-Host "wrote $out"
"""
    with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False, encoding="utf-8") as f:
        f.write(script)
        path = f.name
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", path],
            check=True,
        )
    finally:
        Path(path).unlink(missing_ok=True)


def main() -> None:
    if not DATA.exists():
        raise SystemExit(f"missing {DATA} — run: npm run prepare-data")
    lines = lines_from_storyboard()
    print(f"VO lines from storyboard: {len(lines)}")
    for i, line in enumerate(lines, 1):
        print(f"  {i}. {line[:80]}")
    speak_windows(lines, OUT)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
