# Tier 2 — Bring us a brand

The exercises in `CURRICULUM.md` take about half an hour and prove you can operate the
machine. This is the other thing: proof you can **take the system to a company it has never
seen.** That is the actual job, and it is what the seat is decided on.

**This is paid work at your Round 1 rate, not another test.** If you are reading this, you
have already been selected. Nothing here is speculative and nothing you build is thrown away.

Budget about a day. There is no clock.

---

## The situation

You are handed a real business. Nobody has written you a spec. Nobody is going to tell you
what its rules are, which channels it belongs on, or what it must never sound like.

You have one thing: **a working reference.** `brands/temerarii-media/` is a complete brand
package for a business you can read about in its own copy. `brands/northgate-home/` is a
second one, built as its deliberate opposite — B2C not B2B, March fiscal year not January,
banning fear where the other bans hype.

Your job is to study those two, work out what actually makes a brand package, and then
build a third for a business of **your own choosing**.

## Choose the business yourself

Pick any real or plausible company. A dental practice, a regional logistics firm, a games
studio, a nonprofit, your last employer, something you would like to start.

Two rules:

1. **It must be genuinely unlike both existing brands.** If it is another agency, or another
   local trade business, you have chosen the easy path and the work will show it.
2. **It must be a business you can reason about.** You need to know what its customers care
   about and what would make them distrust it. That second one is the harder half.

Tell us in one paragraph what you picked and why, before any code.

---

## What to build

### 1 · The brand package

```
brands/<your-brand>/
  governance/brand.json
  content/_context/GOAL.yaml
  content/_context/calendar/<campaign>.yaml
```

Read the two existing packages to work out what belongs in each file. That reading **is** the
exercise — we deliberately have not given you a template, because deriving the shape from
working examples is the skill this seat is for.

The part that carries the most weight is **`voice.banned_words`**.

Do not copy either existing list. Temerarii bans hype because a studio selling AI has to
sound quieter than its competitors. Northgate bans fear and pressure because a home-services
company that frightens people gets one job and no second call. **Neither list would work for
the other business.**

So: what must *your* business never sound like? Not "unprofessional" — specifically, what is
the failure mode that would make its particular customers stop trusting it? Fifteen to thirty
terms, and be ready to defend any of them.

### 2 · Make it run

```bash
BRAND=<your-brand> python -m pipeline.gates
BRAND=<your-brand> python -m pipeline.publish --week <n> --dry-run
```

Every gate green. Real payloads for every channel you declare.

**You should not need to modify anything in `pipeline/`.** That is the claim the whole system
rests on: a brand is a data package, so adding one is a data change.

**If that claim turns out to be false — if you hit something that only works for the existing
brands — then finding it is the most valuable thing you will do all week.** Do not quietly
work around it. Fix it, and add the gate that catches it next time. Say so in your PR. Five
bugs of exactly that kind were found this way while this kit was being built, and each one
became a permanent check.

### 3 · Author one week

One week, every channel you declared, native copy for each surface.

Not the same sentence fifteen times. A 280-character post is not an email subject; an email
is not a podcast description. `pipeline/content.py` maps channels to authored fields — read
it to see what each surface expects.

`channel_coverage` will fail if you declare a channel and author nothing for it. That gate
exists because this pipeline once used the week's tagline as the body for *every* channel: it
passed validation, the mock accepted all fifteen, and the output was fifteen identical posts.
Nothing failed, so nothing got fixed.

### 4 · Add a gate

Pick a rule that matters for **your** business and enforce it in `pipeline/gates.py`.

Requirements:

- It fails on a real problem and passes on correct data
- It names the offending week and field — a gate that says "something is wrong" is barely
  better than no gate
- Its docstring says **why it exists**, in terms of what goes wrong without it
- It runs for every brand, including the two you did not write

Examples, if you want a start: a claim like a price or a guarantee appearing without a
qualifier; a required disclosure missing from a regulated category; a CTA on a channel where
it is not allowed; two consecutive weeks reusing the same hook.

**This is the single strongest signal in the submission.** Everything else shows you can
follow a system. This shows you would improve one.

---

## For the Creative Lead

Everything above, plus:

### 5 · Author from a brief, not from an example

Write your week from your own business brief. Do not adapt Northgate's copy — the seams show
immediately and we will see them.

Each cell records a **strategic intent**. Fill it in honestly: what is this week *for*? A
week that cannot say what it is for is decoration.

### 6 · Review a week that is not yours

`brands/northgate-home/` week 11 has problems beyond the planted banned words: weak intent,
a hook that repeats, at least one cell doing no work.

Write **execution-ready revision notes** — the kind an operator can act on without a meeting.
Not "make this punchier". Which cell, what is wrong, what to change it to.

We are reading for whether your notes could be handed to someone else and executed. That is
the difference between an editor and a critic, and this seat is the first one.

### 7 · Switch brands and stay right

Take one piece of copy you wrote for your brand and rewrite it for **Northgate**, then for
**Temerarii**. Same idea, three sets of rails.

Two of the three will fight you. Say which, and why. That friction is the job.

---

## For the Technical Operator

Everything in 1–4, plus:

### 5 · Fix the broken branch

```bash
git checkout tier2/broken
python -m pipeline.gates --brand northgate-home
```

Three things are wrong. One fails a gate loudly. One produces a wrong answer while every
gate passes. One is only visible if you compare output against what the data actually says.

For each: what it was, how you found it, and — for at least one — **the gate you added so it
cannot happen again.**

The middle bug is the point of the exercise. Anything that fails loudly gets fixed by
whoever hits it. The dangerous defects are the ones that return a plausible answer, and the
only defense is a check that knows what right looks like.

### 6 · Prove the dirty set is minimal

Change one field in one week. Show which assets that invalidates, and defend that it is the
**smallest correct set** — not the safe one.

"Re-render everything" is always correct and always wrong. It turns a thirty-second fix into
an hour, every time, and the cost compounds silently.

---

## Not in this kit

**Rendering.** The real pipeline renders video with Remotion — one source to 9:16 and 16:9,
audio muxed to −16 LUFS. It is a substantial part of the job and it is **deliberately absent
here**, because it needs headless Chrome and a working render path, and we would rather test
your judgment than your ability to install a toolchain.

You will be trained on it. It is not a hidden requirement, and not knowing it now costs you
nothing.

---

## Submitting

A PR against your own fork with:

- **One paragraph** on the business you chose and why
- **Your brand package**, gates green
- **Your gate**, with its docstring
- **Anything you had to change in `pipeline/`** — called out explicitly. This is a finding,
  not an admission
- Creative: your revision notes and the three-rails rewrite
- Technical: the three bugs, how you found each, and the gate you added

## What decides it

Not the scorecard. By this point everyone's is green.

- **Did the banned-word list show you understood the business,** or is it a generic list of
  words nobody likes?
- **Did you add a gate that we would keep?**
- **When something did not work, did you fix the instance or the class?**
- **Can someone else act on what you wrote** without asking you a question?

The last one decides more seats than any of the others.
