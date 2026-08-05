"""The gates — every rule the system will not let you break.

    python -m pipeline.gates                     # all gates, active brand
    python -m pipeline.gates --brand northgate-home
    python -m pipeline.gates --gate placement

Exit 0 = every gate passed. Exit 1 = at least one failed, and the output names which.

THE DISCIPLINE THIS ENCODES: every bug becomes a permanent gate. When something breaks
in a way a person had to notice, you have learned that people do not reliably notice it.
The fix is not to be more careful next time — it is to write the check that fails loudly
the next time, forever, and to do it in the same change as the fix.

Each gate below exists because the corresponding mistake actually happened.
"""
from __future__ import annotations

import argparse
import sys
from collections.abc import Callable

from .brand import active_brand, brand_json
from .calendar import campaign_weeks, campaigns, load_all, load_campaign, load_goal
from .content import resolve, unauthored
from .schedule import NUM_WEEKS, fiscal_label
from .voice import scan_brand

Result = tuple[bool, list[str]]


def gate_placement(brand: str) -> Result:
    """Authored week keys must match what GOAL.yaml actually places.

    WHY: a campaign's `start_week` was bumped to postpone it, but the authored weeks in
    calendar/*.yaml were never moved. Every campaign then rendered one story while its
    video showed another — a mismatch of exactly four weeks that nothing detected,
    because the other checks compared placement-derived data to placement-derived data
    and never looked at the calendar's absolute week keys.
    """
    problems: list[str] = []
    for c in campaigns(brand):
        cid = c.get("id")
        if not cid:
            problems.append("a campaign in GOAL.yaml has no id")
            continue
        placed = set(campaign_weeks(cid, brand))
        authored = set(load_campaign(cid, brand))
        if not authored:
            continue
        if stray := sorted(authored - placed):
            problems.append(
                f"{cid}: authored weeks {stray} are not placed by GOAL.yaml "
                f"(placed: {sorted(placed)})")
    return (not problems), problems


def gate_year_boundary(brand: str) -> Result:
    """No authored week may exceed 52 without the fiscal label proving it is handled.

    WHY: `place()` used to clamp at 52, so a campaign starting late in the year resolved
    to NO weeks at all and vanished silently while its copy sat on disk. Weeks past 52
    are legitimate — they are next year — but they must be LABELLED as next year, never
    rendered as a phantom "week 54".
    """
    problems: list[str] = []
    for wk in sorted(load_all(brand)):
        if wk > NUM_WEEKS:
            label = fiscal_label(wk, 2026)
            if label.endswith(f"W{wk:02d}"):
                problems.append(f"week {wk} labelled {label} — should roll into next year")
    return (not problems), problems


def gate_completeness(brand: str) -> Result:
    """Every authored week needs the fields the downstream stages read."""
    problems: list[str] = []
    for wk, wd in sorted(load_all(brand).items()):
        for field in ("name", "tagline"):
            if not getattr(wd, field):
                problems.append(f"W{wk} ({wd.campaign_id}): missing {field}")
    return (not problems), problems


def gate_voice(brand: str) -> Result:
    """No authored cell may contain one of THIS brand's banned terms."""
    v = scan_brand(brand)
    return (not v), [f"W{x['week']} {x['campaign']}/{x['field']}: banned {x['word']!r}"
                     for x in v]


def gate_brand_package(brand: str) -> Result:
    """A brand must carry its own rails — never inherit another brand's by accident.

    WHY: a loader read the repo-root brand.json unconditionally, so scanning a second
    brand silently enforced the FIRST brand's rules. It passed every planted violation
    and reported success. A gate that is wrong is worse than no gate.
    """
    problems: list[str] = []
    bj = brand_json(brand)
    if not (bj.get("voice") or {}).get("banned_words"):
        problems.append(f"{brand}: governance/brand.json has no voice.banned_words")
    if not bj.get("channels"):
        problems.append(f"{brand}: governance/brand.json has no channels")
    if not bj.get("name"):
        problems.append(f"{brand}: governance/brand.json has no name")

    # A brand with no GOAL.yaml places no campaigns — so gate_placement has nothing to
    # compare and passes VACUOUSLY. That is how an incomplete brand package sailed through
    # a full green run here: every gate reported PASS because the data they check was
    # absent, not correct. Assert the package EXISTS before trusting checks made against it.
    if not load_goal(brand):
        problems.append(f"{brand}: no content/_context/GOAL.yaml — without it the placement "
                        f"gate has nothing to check and passes vacuously")
    elif not campaigns(brand):
        problems.append(f"{brand}: GOAL.yaml places no campaigns")
    return (not problems), problems


def gate_channel_coverage(brand: str) -> Result:
    """Every channel a brand DECLARES must have authored content in every authored week.

    WHY: publish once used the week's tagline as the body for every channel. Nothing
    failed — payloads built, validation passed, the mock accepted all of them — and the
    result was fifteen identical posts going out under a client's name. A pipeline that
    cannot tell "authored for this surface" from "filled in with whatever was nearby" is
    not a pipeline, and the absence of an error is exactly what made it survive.

    Declaring a channel is a commitment to author for it. If a brand does not publish to
    podcasts, the fix is to remove it from the package — not to let the week ship silence.
    """
    from .publish import channels  # local import: publish imports calendar, avoid a cycle

    declared = channels(brand)
    problems: list[str] = []
    for wk, wd in sorted(load_all(brand).items()):
        if missing := unauthored(wd, declared):
            problems.append(f"W{wk} ({wd.campaign_id}): no authored content for "
                            f"{', '.join(missing)}")
    return (not problems), problems


def gate_channel_limits(brand: str) -> Result:
    """Authored copy must fit the platform it is bound for.

    Over-length copy is not rejected by most platforms — it is TRUNCATED, silently, often
    mid-word and usually right where the link was. Catching it here costs nothing;
    catching it after publication costs the post.
    """
    from .content import over_limit
    from .publish import channels

    declared = channels(brand)
    problems: list[str] = []
    for wk, wd in sorted(load_all(brand).items()):
        for ch in declared:
            hit = resolve(wd, ch)
            if not hit:
                continue
            body, field = hit
            if limit := over_limit(body, ch):
                problems.append(f"W{wk} {field} -> {ch}: {len(body)} chars, limit {limit}")
    return (not problems), problems


GATES: dict[str, Callable[[str], Result]] = {
    "placement": gate_placement,
    "channel_coverage": gate_channel_coverage,
    "channel_limits": gate_channel_limits,
    "year_boundary": gate_year_boundary,
    "completeness": gate_completeness,
    "voice": gate_voice,
    "brand_package": gate_brand_package,
}


def run(brand: str, only: str | None = None) -> int:
    names = [only] if only else list(GATES)
    if only and only not in GATES:
        raise SystemExit(f"unknown gate {only!r}. available: {', '.join(GATES)}")
    print(f"GATES — brand={brand}\n")
    failed = 0
    for name in names:
        # A gate that RAISES is a failed gate, not a dead run. Letting the exception
        # escape kills every gate after it, so one loud bug hides all the quiet ones —
        # you fix the crash, re-run, and discover the next problem you could have seen
        # ten minutes earlier. Report it and keep going.
        try:
            ok, problems = GATES[name](brand)
        except Exception as e:
            ok, problems = False, [f"raised {type(e).__name__}: {e}"]
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            failed += 1
            for p in problems[:10]:
                print(f"          - {p}")
            if len(problems) > 10:
                print(f"          ... and {len(problems) - 10} more")
    print()
    if failed:
        print(f"GATES FAIL — {failed} of {len(names)} gate(s) failed.")
        return 1
    print(f"GATES PASS — {len(names)}/{len(names)}.")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run the gates.")
    ap.add_argument("--brand", default=None)
    ap.add_argument("--gate", default=None, help=f"one of: {', '.join(GATES)}")
    a = ap.parse_args(argv)
    return run(active_brand(a.brand), a.gate)


if __name__ == "__main__":
    sys.exit(main())
