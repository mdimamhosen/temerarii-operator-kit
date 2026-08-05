"""Brand resolution — the one place that knows where a brand's data lives.

THE CENTRAL IDEA OF THIS KIT: the engine is brand-AGNOSTIC. A brand is a DATA PACKAGE,
not a special case in the code. Everything downstream — calendars, gates, renders,
publishing — takes a brand argument and reads from `brands/<name>/`.

If you only learn one thing here, learn this: any function that needs brand-specific
information must TAKE THE BRAND AS AN ARGUMENT. The moment a function reaches for a
default instead, it works perfectly for the first brand and silently serves the wrong
data to the second. That failure is invisible in testing with one brand, and it is the
single most common bug in systems like this one.

    BRAND=northgate-home python -m pipeline.voice --week 12

Exercise 4 in CURRICULUM.md is a real instance of that bug. It is not hypothetical — it
shipped in the system this kit is modelled on, and the fix is the one described here.
"""
from __future__ import annotations

import functools
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_BRAND = "temerarii-media"


def active_brand(requested: str | None = None) -> str:
    """Resolve the brand: explicit argument wins, then $BRAND, then the default."""
    if requested and requested.strip():
        return requested.strip()
    return (os.environ.get("BRAND") or DEFAULT_BRAND).strip() or DEFAULT_BRAND


def brand_root(brand: str | None = None) -> Path:
    """`brands/<name>/`. Raises rather than silently falling back — a typo in a brand
    name should fail loudly, not quietly serve you a different brand's content."""
    b = active_brand(brand)
    root = REPO / "brands" / b
    if not root.is_dir():
        available = sorted(p.name for p in (REPO / "brands").iterdir() if p.is_dir())
        raise SystemExit(f"unknown brand {b!r}. available: {', '.join(available)}")
    return root


def brand_path(rel: str, brand: str | None = None) -> Path:
    return brand_root(brand) / rel


def list_brands() -> list[str]:
    return sorted(p.name for p in (REPO / "brands").iterdir() if p.is_dir())


_brand_cache: dict | None = None


def brand_json(brand: str | None = None) -> dict:
    global _brand_cache
    if _brand_cache is not None:
        return _brand_cache
    """A brand's governance/brand.json.

    NOTE the cache key: `brand`. Caching this globally instead — one module-level dict
    filled by whichever brand was loaded first — is exactly the bug in Exercise 4.
    """
    b = active_brand(brand)
    p = brand_path("governance/brand.json", b)
    if not p.exists():
        raise SystemExit(f"{b}: missing governance/brand.json at {p}")
    # utf-8-sig, not utf-8: a Windows editor (or PowerShell's `Set-Content -Encoding utf8`)
    # writes a byte-order mark that makes json.loads fail on column 1 with an error that
    # says nothing about encoding. Read it tolerantly instead of losing an hour to it.
    _brand_cache = json.loads(p.read_text(encoding="utf-8-sig"))
    return _brand_cache


def banned_words(brand: str | None = None) -> list[str]:
    """The brand's banned words, lowercased.

    These differ per brand ON PURPOSE and they are not variations on a theme:
    temerarii-media bans HYPE ("revolutionary", "game-changer"); northgate-home bans
    FEAR-SELLING and PRESSURE ("act now", "silent killer"). A reviewer who has only
    pattern-matched "no superlatives" catches nothing on the second brand.
    """
    voice = brand_json(brand).get("voice") or {}
    return [w.lower() for w in (voice.get("banned_words") or [])]
