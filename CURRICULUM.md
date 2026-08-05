# Curriculum

Six exercises, in order. Each is graded by `training/grade.py`, which you can run as many
times as you want. There is no hidden test — the grader in this repo is the grader we use.

Write answers into `training/answers/` where asked. That directory is gitignored here so
the reference repo carries no answer key; commit it in **your fork** so we can see it.

```bash
python training/grade.py              # everything
python training/grade.py --exercise 3 # just one
```

A fresh clone scores **5/6**. Exercise 5 is the one waiting on you.

---

## 1 · Both brands load, and their gates pass

**Run:**
```bash
BRAND=temerarii-media  python -m pipeline.gates
BRAND=northgate-home   python -m pipeline.gates
```

Everything passes except `voice` on `northgate-home` — that brand ships with three
planted violations, which is exercise 4.

**Understand before moving on:** open `pipeline/gates.py` and read the docstring on each
gate. Every one of them exists because the mistake it catches actually happened in
production. `gate_placement` in particular describes a bug where a campaign was postponed
by bumping one number, the authored weeks were not moved with it, and for weeks every
campaign rendered one story while its video showed another. Nothing detected it, because
the checks in place compared derived data against derived data.

**The habit that matters:** when something breaks in a way a person had to *notice*, you
have learned that people do not reliably notice it. Write the gate in the same change as
the fix.

---

## 2 · Fiscal weeks

`pipeline/schedule.py` implements a 4-4-5 retail calendar. Weeks run 1–52, always start
Sunday, and the anchor comes from each brand's `GOAL.yaml` — which is why one brand's year
opens in January and the other's in March with no branch in the code.

**Answer for yourself, then check with the grader:**
- What is week 53 of a 2026 anchor?
- Which quarter is week 53 in?
- What does `place(50, 6)` return?

**The trap:** `place()` used to stop at week 52. A campaign starting at week 50 therefore
resolved to *no weeks at all* — it did not error, it did not warn, it returned an empty
list, and the copy sat authored on disk while the campaign silently never shipped. Weeks
past 52 are legitimate; they are next year. `fiscal_label(53, 2026)` is `2027-W01`.

An empty result is a suspicious result. Code that can return "nothing" for a reasonable
input should say so out loud.

---

## 3 · The rails are per brand

**Run:**
```bash
python -c "from pipeline.brand import banned_words; print(len(banned_words('temerarii-media')), len(banned_words('northgate-home')))"
```

Read both `governance/brand.json` files. The lists are not variations in strictness, they
are **opposites**: one bans hype, the other bans fear and pressure.

**Now the real question.** In `pipeline/brand.py`, `brand_json()` is cached with
`@functools.lru_cache` keyed on the brand. Suppose it were cached in a single
module-level dict instead, filled by whichever brand loaded first.

- What would `python -m pipeline.voice --brand northgate-home` report, if
  `temerarii-media` had been loaded earlier in the same process?
- Would you get an error?

You would not. You would get **PASS**, on copy containing planted violations, because
the gate would be checking the wrong brand's list. This exact bug shipped in the system
this kit is modelled on. It was found only because someone ran a second brand through it
and noticed the planted violations were not firing.

A gate that is silently wrong is worse than no gate. No gate leaves you appropriately
nervous; a wrong gate manufactures confidence.

---

## 4 · Find the planted violations

`northgate-home` contains **three** deliberate voice violations.

```bash
python -m pipeline.voice --brand northgate-home
```

Write `training/answers/violations.txt`, one per line, as `week field banned-term`:

```
10 days.Mon.social[2] dangerous
```

**Then look harder than the tool did.** One of the three is the word `dangerous` in the
sentence *"Our technicians are not busier in spring because spring is dangerous."* That is
a **negation** — the copy is arguing against fear-selling, and the word list flagged it
anyway.

So: is it a violation?

There is a defensible answer either way, and we care about the reasoning. Add a few lines
at the bottom of your `violations.txt` saying what you would do and why. A word list
catches words; it cannot catch intent. Knowing where the tool stops is most of the skill —
an operator who defers to the gate on everything is as much of a problem as one who
overrides it.

---

## 5 · A minimal dirty set

Suppose you edit **week 11's `tagline`** in `northgate-home`.

Which authored weeks now need re-rendering?

Write the answer as a JSON array in `training/answers/dirty_set.json`, e.g. `[7, 9]`.

**Read this before answering.** The grader rejects an answer containing every authored
week, even though "everything is stale" is technically safe. A dirty set that always
returns everything is not a dirty set — it is the absence of one, and it turns a
thirty-second fix into a full re-render. The entire value is in naming *only* what
actually changed.

Being conservative is not free. It is a real cost, paid every time.

---

## 6 · Publish payloads

```bash
python -m pipeline.publish --week 10 --brand northgate-home --dry-run
python mock-api/server.py       # in another terminal
python -m pipeline.publish --week 10 --brand northgate-home --post
```

The mock enforces what the real service enforces: required fields, per-channel length
limits, `utm_campaign` on every link, and `source.campaign` on every payload.

**That last one is the rule worth internalising.** Every published item must trace back to
a registry entry. Not because a policy says so — because in six months someone will ask
where a post came from, and "I am not sure" is not an answer you want to give about your
own work. The check lives in code so that an unattributable payload is impossible to
construct, rather than merely discouraged.

**Notice what you did not have to configure.** Every brand runs the same base channel
calendar — all social, long form, blog, email, SMS — but `northgate-home` also publishes a
**podcast**, and you did not tell it that. It came from the brand package. Adding a channel
is an edit to `governance/brand.json`, never a pipeline change. That is the whole point of
exercises 1 and 3.

**And notice what did not get sent.** `northgate-home` lists Nextdoor as `manual`: a real
channel with a real audience and no publish API. Its payload is still built, still
validated, and reported as needing a human — the mock will **refuse** it if you try to post
it, deliberately.

It would have been easier to leave manual channels out of the plan entirely. That is the
wrong trade. A channel that silently disappears from the calendar is not noticed for weeks,
and the failure surfaces as "why did we stop posting there?" long after the cause is cold.
Work that needs a human is still work; it belongs on the plan, marked.

---

## What we are actually reading

The scorecard is the floor, not the ceiling. Passing 6/6 shows you can operate the
machine. What we are looking for beyond that:

- **Exercise 4's written note.** Judgment about where a tool stops.
- **Whether you added a gate.** If you found something the gates do not catch, the
  strongest possible submission adds the gate that catches it. That is the single most
  valuable instinct in this job.
- **Your commits.** Small, legible, each one explaining *why*. We read them.
