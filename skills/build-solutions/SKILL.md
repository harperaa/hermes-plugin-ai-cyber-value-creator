---
name: build-solutions
description: >
  Turn the ICP's validated problems into a concrete list of candidate solutions
  (which double as Video/Ad topics). Use during the Create Value foundation,
  step 3 (Solutions), after problems are confirmed.
metadata:
  tags: [solutions, offers, content-topics, gtm, cyber-value-creator]
  always_load: false
---

# Build Solutions

Generate a list of distinct candidate **solutions** — each a mechanism that
delivers the ICP's dream outcome or removes a validated problem. Be directive and
deterministic. These solutions double as the Video/Ad topics for Attract, and feed
directly into offer design. When finished, call `record_company_context`
(field: `solutions`).

> Prerequisite: the prioritized problems must be confirmed (see `research-problems`
> / the Company Context `problems` field). If not, complete that first.

---

## Step 1 — Load ICP + problems

Recall the current ICP and the prioritized problems from the Company Context.
Restate the top 3–5 problems — every solution must trace to one of them.

## Step 2 — Generate solutions per problem

For each validated problem, produce 2–3 candidate solutions. A solution is a
**mechanism** (a specific way to get the result), not a vague promise. For each,
capture all of:

- **Name** — short, outcome-oriented.
- **Problem it solves** — which validated problem (by name).
- **Mechanism** — how it actually produces the dream outcome (the "secret sauce").
- **Format / delivery** — e.g. done-for-you service, course, group program, tool/
  software, template, workshop, retainer.
- **Why it fits the ICP** — ties to their experience level, time, budget, context.
- **Effort & time to result** — rough effort for the customer + time to value
  (you'll minimize these in offer design).

## Step 3 — Make them distinct + rankable

Ensure the options are genuinely different (different mechanism or format), not
restatements. Then rank them on:

- **Demand** — how many in the ICP want this (from the problem's frequency).
- **Differentiation** — how unique vs. what competitors offer.
- **Deliverability** — how confidently the company can deliver a great result.

Aim for **4–8 distinct, ranked options** the user can choose between.

## Step 4 — Double as content topics

Note that each solution is also a Video/Ad topic for Attract (the mechanism, the
"how", the result). Flag the 3–5 strongest as the first content/ad angles.

## Step 5 — Confirm with the user (the gate)

Present the ranked solutions and ask: *"Which of these excite you? Which feels most
deliverable and differentiated?"* Iterate until the user confirms the shortlist.
**Do not finish without confirmation.** Do not pick the single offer yet — that's
the next step (Make Offers).

## Step 6 — Record it (always do this)

Call `record_company_context` with:
- `field`: `solutions`
- `content`: the ranked solution list (name · problem solved · mechanism · format ·
  why it fits · demand/differentiation/deliverability).

The next step (Make Offers) selects ONE solution and packages it as a Grand Slam
Offer; the rest can be saved as future-offer (draft) projects.
