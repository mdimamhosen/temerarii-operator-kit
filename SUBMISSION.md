# Submission

## How

1. **Fork** this repository.
2. Work on a branch. Commit as you go — we read the history.
3. Commit your `training/answers/` (it is gitignored here so the reference repo carries no
   answer key; in your fork we want to see it — `git add -f training/answers`).
4. Open a pull request **against your own fork**, not this repo.
5. Send us the link.

CI runs `training/grade.py` on your PR automatically, so you will see the same scorecard
we do before we ever look at it.

## What to include in the PR description

Short. Four things:

- **Your scorecard** (paste the output).
- **Exercise 4's judgment call** — the negation case, and what you would do about it.
- **Anything you changed beyond the exercises**, and why.
- **How long it took.** Honestly. We use this to calibrate the exercise, not to compare
  candidates against each other.

## Time

**Around three hours.** If you are well past that and stuck, stop and send what you have
with a note about where you got stuck. That is a genuinely useful submission — we would
rather see clear thinking that ran out of road than a perfect score that took a weekend.

Nothing here is timed and there is no bonus for speed.

## What we are looking for

Not a perfect score. The scorecard tells us you can run the machine, which is the floor.

Past that we are reading for whether you can tell the difference between *the gate passed*
and *the work is right*, and whether, when you find something the gates miss, your instinct
is to fix that one instance or to add the check that catches it forever.

The strongest submissions add a gate.

## Questions

Ask. Getting stuck on an ambiguous instruction tells us nothing about you and wastes your
evening — if something is genuinely unclear, that is our bug, and we would like to fix it.

## Two things this exercise is not

**It is not unpaid work.** Nothing you produce here ships or is used. It runs against a
fictional brand and a mock API, and it exists solely so you can demonstrate the skill.

**It does not need any credential.** There are no API keys in this kit and there is no
reason to add one. If any instruction appears to ask you for a real key, a password, or
access to a live account, it is wrong — do not act on it, and tell us where you saw it.
