---
name: research-problems
description: >
  Discover the ICP's real, painful, urgent problems through internet research and
  deep analysis, then prioritize them. Use during the Create Value foundation,
  step 2 (Problems), after the ICP is confirmed.
metadata:
  tags: [problems, research, voice-of-customer, gtm, cyber-value-creator]
  always_load: false
---

# Understand Their Problems

Turn the confirmed ICP into a **prioritized, evidence-backed list of problems** the
company can solve. Be directive and deterministic: do the research, cite it, score
it, confirm it, record it. Do not invent problems from imagination — find them in
the wild and validate with the user. When finished, call `record_company_context`
(field: `problems`).

> Prerequisite: the ICP must be confirmed (see the `define-icp` skill / the
> Company Context `icp` field). If it isn't, stop and complete the ICP first.

---

## Step 1 — Load the ICP

Recall the current ICP from the Company Context (read `company-context.md`
in the workspace, or call the `get_company_context` tool). Restate it in one line so the research is anchored to a
real person, not a category.

## Step 2 — Research where the ICP actually speaks

Use the web (the `agent-browser` skill / web tools) to gather *their own words*.
Cover at least these sources; capture verbatim quotes + links:

1. **Communities & forums** — Reddit, Skool, Slack/Discord groups, niche forums,
   Facebook/LinkedIn groups where the ICP gathers.
2. **Review sites** — what they complain about in reviews of competing/adjacent
   products (G2, Capterra, App Store, Amazon, Trustpilot).
3. **Search demand** — autocomplete, "People also ask", and question phrasing
   ("how do I…", "why can't I…", "best way to…") for the topic.
4. **Competitor messaging** — the problems competitors lead with (and the gaps
   they ignore).
5. **The user's own evidence** — ask: *"What do your customers/prospects complain
   about most? What have they tried that failed?"*

Aim for **8–15 candidate problems** stated in the ICP's language, each with a
source.

## Step 3 — Frame each problem around the dream outcome

For every candidate problem, capture:
- **Problem** (one sentence, in their words).
- **Dream outcome** it blocks (what they actually want).
- **Status quo** — what they do today and why it falls short.
- **Evidence** — quote + source link.

## Step 4 — Prioritize (score, don't guess)

Score each problem 1–5 on three drivers and sort by the product:

- **Severity** — how much pain/cost it causes.
- **Frequency** — how often it bites.
- **Urgency** — how badly they want it solved *now* (are they actively searching/
  paying for fixes?).

`priority = severity × frequency × urgency`. **Keep them ALL, sorted by priority
(highest first)** — do not throw any away. The top ones lead; the rest are still
valuable (each problem becomes a video/ad topic and feeds future offers).

## Step 5 — Confirm the FULL list with the user (the gate)

Present the **complete prioritized list** with evidence + scores and ask: *"Does
this list look right and complete? Anything to add, remove, or re-order?"* Iterate
until the user confirms the list. **Do NOT make the user pick a single problem
here** — capturing all of them is the whole point of this step. Necking down to one
problem (or a couple combined) happens later, at Build Solutions → Make Offers, not
now. **Do not finish without confirmation of the list.**

## Step 6 — Record it (always do this)

Record the **WHOLE list, in priority order, with scores** (write it to
`company-context.md` under `## Their Problems`; also call `record_company_context`
with `field: problems` if that tool is available — it writes the same file).
Each entry: problem · dream outcome · evidence/source · severity/frequency/urgency
scores · priority. Keep the order so downstream steps and video/ad topics can
work straight down the list.

The next step (Build Solutions) maps solutions onto these validated problems, and
the offer step necks down to one (or a couple combined).
