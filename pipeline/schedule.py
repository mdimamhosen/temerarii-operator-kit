"""The 4-4-5 fiscal retail calendar.

Weeks are numbered 1..52 and always start on a Sunday. Quarters are 13 weeks in a
4-4-5 month pattern. The `anchor` in a brand's GOAL.yaml is the Sunday of week 1, so
two brands can run entirely different fiscal years — northgate-home starts in March,
temerarii-media in January — without a single branch in the code.

WEEKS PAST 52 ARE REAL. A campaign placed near the end of a year runs into the next
one, and week 53 is 2027-W01, not "week 53". Code that clamps at 52 does not raise an
error — it silently produces a campaign with NO weeks, and the content sits on disk
unshipped. That happened in the system this kit is modelled on; `place()` below is
written the way it is because of it.
"""
from __future__ import annotations

from datetime import date, timedelta

NUM_WEEKS = 52
# 4-4-5: months of 4, 4 and 5 weeks, repeating each quarter.
_MONTH_WEEKS = [4, 4, 5] * 4


def week_sunday(anchor: date, week: int) -> date:
    """The Sunday that starts `week`, counting from the anchor. Wraps past 52."""
    return anchor + timedelta(weeks=week - 1)


def fiscal_year_offset(week: int) -> int:
    """How many fiscal years past the anchor year `week` falls in."""
    return (int(week) - 1) // NUM_WEEKS


def year_week(week: int) -> int:
    """The 1..52 week number within its own fiscal year. year_week(53) == 1."""
    return ((int(week) - 1) % NUM_WEEKS) + 1


def fiscal_label(week: int, anchor_year: int) -> str:
    """'2026-W27'. Week 53 of a 2026 anchor is '2027-W01', never '2026-W53'."""
    return f"{anchor_year + fiscal_year_offset(week)}-W{year_week(week):02d}"


def quarter_of(week: int) -> int:
    """1..4, computed from the week's position in its OWN year."""
    return ((year_week(week) - 1) // 13) + 1


def month_of(week: int) -> int:
    """1..12 under the 4-4-5 pattern."""
    w = year_week(week)
    run = 0
    for i, span in enumerate(_MONTH_WEEKS, start=1):
        run += span
        if w <= run:
            return i
    return 12


def place(start_week: int, beats: int, skip_weeks: set[int] | None = None) -> list[int]:
    """Resolve a campaign to concrete week numbers.

    Returns `beats` weeks starting at `start_week`, skipping any week in `skip_weeks`
    (holidays, blackout periods). Postponing a campaign is a one-line change to
    `start_week` — that is the whole point of placing declaratively instead of writing
    week numbers by hand.

    The horizon deliberately extends PAST week 52 rather than clamping to it, so a
    campaign starting at week 50 resolves into the following year instead of quietly
    returning fewer weeks than asked for.
    """
    skip = skip_weeks or set()
    out: list[int] = []
    wk = int(start_week)
    horizon = NUM_WEEKS
    while len(out) < beats and wk <= horizon:
        if wk not in skip:
            out.append(wk)
        wk += 1
    if len(out) < beats:
        raise ValueError(
            f"could not place {beats} beats from week {start_week} "
            f"(only found {len(out)}) — too many skip_weeks?")
    return out
