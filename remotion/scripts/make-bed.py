"""Quiet acoustic-ish bed for the spring-tuneup reel.

Storyboard rail: the bed never swells at the CTA. We keep amplitude flat (slightly
lower) in the last four seconds so the booking card is not sold by the music.
"""
from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "public" / "bed.wav"
SR, DUR, AMP = 44100, 30.0, 0.04


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    n = int(SR * DUR)
    with wave.open(str(OUT), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        for i in range(n):
            t = i / SR
            env = 0.7 + 0.3 * math.sin(2 * math.pi * t / 8.0)
            if t > 26:
                env = 0.55  # no swell at CTA
            s = (
                math.sin(2 * math.pi * 196 * t) * 0.55
                + math.sin(2 * math.pi * 294 * t) * 0.35
                + math.sin(2 * math.pi * 392 * t) * 0.15
            )
            val = int(max(-32767, min(32767, s * env * AMP * 32767)))
            w.writeframes(struct.pack("<h", val))
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
