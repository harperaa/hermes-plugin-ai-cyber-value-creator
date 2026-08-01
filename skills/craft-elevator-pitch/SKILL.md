---
name: craft-elevator-pitch
description: >
  Distill the confirmed Create Value foundation (ICP, problems, solutions, offer)
  into one sharp elevator-pitch sentence. The final foundation step; CEO-run.
metadata:
  tags: [foundation, elevator-pitch, positioning, company-context]
---

# Craft the Elevator Pitch

The last Create Value foundation step. Turn everything the foundation produced into
a single, sharp sentence the whole org can repeat. **You (the CEO) do this yourself
with the user — do not delegate.**

## The shape (use it exactly)

> **I help [brief ICP name] with [problem] [achieve outcome] within [timeframe].**

One plain sentence. No preamble, no markdown, no quotes, no list.

## Step 1 — Read the FULL context

Read all of `company-context.md` (not just the headline fields): the **ICP**, the
**problems**, the **candidate solutions**, the **active offer**, and the confirmed
**niche / outcome / paying avatar / recognition signal**. The pitch must be grounded
in all of it.

## Step 2 — Compose

- **[brief ICP name]** — a short human label, not the full profile (e.g. "laid-off
  software engineers", not the six-dimension description).
- **[problem]** — the sharpest problem the active offer solves (from the problem list).
- **[achieve outcome]** — the dream outcome / end state they want.
- **[timeframe]** — a realistic timeframe drawn from the offer (e.g. "90 days").

Keep it concrete and free of jargon. It should sound like something you'd say out loud.

## Step 3 — Confirm with the user

Show the one sentence and ask if it lands or needs a tweak. Refine until they're
happy. **Do not finish without confirmation.**

## Step 4 — Record it

Write the confirmed sentence into `company-context.md` under the `## Elevator Pitch`
section (replace any placeholder). If the `record_company_context` tool is available
in your runtime, also call it with `field: elevatorPitch` — it writes the same file;
don't block on it, the file is the source of truth.

Completing this lays the foundation to enter the flywheel laps.
