"""Build publish payloads from authored cells, and (optionally) post them to the mock API.

    python -m pipeline.publish --week 27 --dry-run
    python -m pipeline.publish --brand northgate-home --week 12 --post

THE RULE THIS ENFORCES: every published item traces back to a registry entry. A payload
with no `source` is refused here, before it ever reaches a network call. "Where did this
post come from?" must have an answer six months later, and the only reliable way to get
one is to make an unattributable payload impossible to construct.

Channels are per-brand and are NOT the same set. temerarii-media runs nine social
channels; northgate-home is a local trade business and runs Google Business Profile,
local SEO, Nextdoor, email and SMS — it has no business on X or Bluesky. Hardcoding a
channel list is the same class of bug as hardcoding a banned-word list.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

from .brand import active_brand, brand_json
from .calendar import anchor_date, load_all
from .content import LIMITS, resolve, unauthored
from .schedule import fiscal_label, week_sunday
from .utm import build_utm

MOCK_API = "http://127.0.0.1:8787/publish"


def channels(brand: str | None = None) -> list[str]:
    """Every channel this brand publishes to, in declaration order.

    Reads whatever groups the brand package defines rather than looking for specific key
    names. Brands currently share one channel calendar grouped as social / longform /
    owned, but a package that regroups them — or adds a group — must keep working without
    a code change. That is the whole contract: the pipeline knows there ARE channels, and
    the brand package alone decides which.
    """
    ch = brand_json(brand).get("channels") or {}
    out: list[str] = []
    for key, val in ch.items():
        # `_`-prefixed keys are internal commentary in the brand package, never data.
        if str(key).startswith("_") or not isinstance(val, list):
            continue
        out.extend(str(c) for c in val if not str(c).startswith("_"))
    return list(dict.fromkeys(out))  # dedupe, preserve order


def manual_channels(brand: str | None = None) -> set[str]:
    """Channels with no publish API — delivered by a human.

    These are real destinations, not second-class ones. Nextdoor is where a local trade
    brand's audience actually is; a podcast host may want a human in the loop. What they
    have in common is that no API call ships them.

    They are still built and still validated. The alternative — omitting them — means the
    channel quietly falls off the calendar and nobody notices for a month. A payload that
    is marked `manual` appears in the plan, gets checked against the same rules, and shows
    up on someone's list. Marking work as needing a human is not the same as skipping it.
    """
    ch = brand_json(brand).get("channels") or {}
    return {str(c) for c in (ch.get("manual") or []) if not str(c).startswith("_")}


def build_payloads(week: int, brand: str | None = None) -> list[dict]:
    b = active_brand(brand)
    weeks = load_all(b)
    if week not in weeks:
        raise SystemExit(f"{b}: week {week} is not authored. "
                         f"authored weeks: {sorted(weeks) or 'none'}")
    wd = weeks[week]
    anchor = anchor_date(b)
    label = fiscal_label(week, anchor.year)
    manual = manual_channels(b)
    out: list[dict] = []
    for ch in channels(b):
        # Native copy per surface. resolve() returns None rather than inventing text —
        # an earlier version used the week's tagline for EVERY channel, which "worked"
        # and produced fifteen identical posts. Unauthored channels are simply absent
        # here and are caught loudly by the channel_coverage gate.
        hit = resolve(wd, ch)
        if hit is None:
            continue
        body, field = hit
        out.append({
            "brand": b,
            "channel": ch,
            "week": week,
            "fiscal_label": label,
            "scheduled_for": week_sunday(anchor, week).isoformat(),
            "body": body,
            "link": build_utm(brand=b, campaign=wd.campaign_id, channel=ch, week=week),
            # "api" ships on --post; "manual" is built, validated and listed for a human.
            "delivery": "manual" if ch in manual else "api",
            # The traceability contract — the ACTUAL authored field, never synthesised.
            "source": {"campaign": wd.campaign_id, "week": week, "field": field},
        })
    return out


def validate(payloads: list[dict]) -> list[str]:
    """Local checks, run BEFORE any network call — a bad payload should never be sent."""
    errs: list[str] = []
    for p in payloads:
        who = f"{p.get('channel', '?')}/W{p.get('week', '?')}"
        if not p.get("body"):
            errs.append(f"{who}: empty body")
        if not p.get("source"):
            errs.append(f"{who}: missing source — every item must trace to a registry entry")
        limit = LIMITS.get(p.get("channel", ""))
        if limit and len(p.get("body", "")) > limit:
            errs.append(f"{who}: body is {len(p['body'])} chars, limit is {limit}")
        if not str(p.get("link", "")).startswith("http"):
            errs.append(f"{who}: link is not a URL")
    return errs


def post(payloads: list[dict], url: str = MOCK_API) -> int:
    """Send the API-delivered payloads. Manual ones are reported, never silently dropped."""
    manual = [p for p in payloads if p.get("delivery") == "manual"]
    if manual:
        print(f"  {len(manual)} payload(s) need a human — not sent:")
        for p in manual:
            print(f"    - {p['channel']}: {p['body'][:60]}")
    ok = 0
    for p in [x for x in payloads if x.get("delivery") != "manual"]:
        req = urllib.request.Request(
            url, data=json.dumps(p).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                if r.status == 200:
                    ok += 1
                else:
                    print(f"  {p['channel']}: HTTP {r.status}")
        except urllib.error.HTTPError as e:
            print(f"  {p['channel']}: HTTP {e.code} — {e.read().decode('utf-8')[:200]}")
        except urllib.error.URLError as e:
            raise SystemExit(f"mock API unreachable at {url} ({e.reason}). "
                             f"Start it: python mock-api/server.py") from e
    return ok


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build and validate publish payloads.")
    ap.add_argument("--brand", default=None)
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--post", action="store_true", help="send to the mock API")
    ap.add_argument("--dry-run", action="store_true", help="print payloads, send nothing")
    ap.add_argument("--out", default=None, help="write payloads to a JSON file")
    a = ap.parse_args(argv)

    b = active_brand(a.brand)
    payloads = build_payloads(a.week, b)
    n_manual = sum(1 for p in payloads if p.get("delivery") == "manual")
    print(f"PUBLISH — brand={b} week={a.week} · {len(payloads)} payload(s) "
          f"across {len(channels(b))} channel(s)"
          + (f" ({n_manual} manual)" if n_manual else ""))

    errs = validate(payloads)
    if errs:
        print(f"\nVALIDATION FAIL — {len(errs)} problem(s):")
        for e in errs:
            print(f"  - {e}")
        return 1
    print("validation OK")

    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(payloads, f, indent=2)
        print(f"wrote {a.out}")
    if a.dry_run:
        print(json.dumps(payloads, indent=2)[:2000])
        return 0
    if a.post:
        # Count against the API-delivered set, not the total. A manual channel that was
        # correctly held back is a success, and exiting non-zero for it would train
        # everyone to ignore this command's exit code.
        sendable = [p for p in payloads if p.get("delivery") != "manual"]
        ok = post(payloads)
        print(f"accepted {ok}/{len(sendable)} sent"
              + (f" · {len(payloads) - len(sendable)} held for manual delivery"
                 if len(sendable) != len(payloads) else ""))
        return 0 if ok == len(sendable) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
