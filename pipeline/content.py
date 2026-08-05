"""Which authored field feeds which channel.

A studio does not write one sentence and blast it everywhere. It writes NATIVE copy per
surface: a 280-character post is not an email subject, an email is not a podcast
description, and a 9:16 short is not a ten-minute YouTube outline. This module is the map
between what a Creative Lead authors and what each channel actually publishes.

    CHANNEL          <- AUTHORED FIELD
    x, linkedin, ... <- days.<Day>.social[n]      native short-form posts
    youtube          <- days.<Day>.short          9:16 vertical script/caption
    youtube_longform <- days.<Day>.longform       long-form title + outline
    podcast          <- days.<Day>.podcast        episode title + description
    blog             <- weeks.<n>.blog            the week's article
    email            <- days.<Day>.email_subject + email_body
    sms              <- days.<Day>.sms            <=160 chars, hard limit
    nextdoor         <- days.<Day>.social[0]      manual delivery, still authored

WHY THERE IS NO SILENT FALLBACK
An earlier version used the week's tagline as the body for EVERY channel. Everything
"worked" — payloads built, validation passed, the mock accepted them — and the output was
fifteen identical posts. Nothing failed, so nothing got fixed.

`resolve()` returns None when a channel has no authored content, and the completeness gate
turns that into a visible failure. An unauthored channel should be loud, because the
alternative is shipping filler under a client's name.
"""
from __future__ import annotations

from .calendar import Week

# Channels that publish native short-form social copy, drawn from `social[]`.
SOCIAL_CHANNELS = {
    "x", "linkedin", "instagram", "facebook", "threads", "bluesky", "pinterest",
    "tiktok", "nextdoor",
}

# Hard platform limits. Exceeding one is a silent truncation at the platform.
LIMITS = {"sms": 160, "x": 280, "bluesky": 300}


def _days_in_order(wd: Week) -> list[tuple[str, dict]]:
    out = []
    for day, slot in (wd.days or {}).items():
        if isinstance(slot, dict):
            out.append((str(day), slot))
    return out


def resolve(wd: Week, channel: str) -> tuple[str, str] | None:
    """Return (body, source_field) for a channel, or None if nothing is authored.

    Deliberately returns None rather than inventing text. The caller decides whether an
    unauthored channel is a warning or a failure; this function never papers over it.
    """
    ch = str(channel)

    if ch == "blog":
        if wd.blog:
            return wd.blog, "blog"
        return None

    if ch == "email":
        for day, slot in _days_in_order(wd):
            subject = slot.get("email_subject") or slot.get("email")
            if subject:
                return str(subject), f"days.{day}.email_subject"
        return None

    if ch == "sms":
        for day, slot in _days_in_order(wd):
            if slot.get("sms"):
                return str(slot["sms"]), f"days.{day}.sms"
        return None

    if ch == "youtube":
        for day, slot in _days_in_order(wd):
            if slot.get("short"):
                return str(slot["short"]), f"days.{day}.short"
        return None

    if ch == "youtube_longform":
        for day, slot in _days_in_order(wd):
            if slot.get("longform"):
                return str(slot["longform"]), f"days.{day}.longform"
        return None

    if ch == "podcast":
        for day, slot in _days_in_order(wd):
            if slot.get("podcast"):
                return str(slot["podcast"]), f"days.{day}.podcast"
        return None

    if ch in SOCIAL_CHANNELS:
        # Social posts are authored as a list per day; channels draw from it in order so
        # the same week does not publish the identical sentence to nine platforms.
        posts: list[tuple[str, str]] = []
        for day, slot in _days_in_order(wd):
            raw = slot.get("social")
            if isinstance(raw, str) and raw.strip():
                posts.append((raw, f"days.{day}.social"))
            elif isinstance(raw, (list, tuple)):
                for i, p in enumerate(raw):
                    if isinstance(p, str) and p.strip():
                        posts.append((p, f"days.{day}.social[{i}]"))
        if not posts:
            return None
        return posts[0]

    return None


def unauthored(wd: Week, channels: list[str]) -> list[str]:
    """Channels a brand declares but this week has no content for."""
    return [c for c in channels if resolve(wd, c) is None]


def over_limit(body: str, channel: str) -> int | None:
    """The limit a body exceeds, or None. Checked before anything is sent."""
    limit = LIMITS.get(str(channel))
    return limit if limit and len(body) > limit else None
