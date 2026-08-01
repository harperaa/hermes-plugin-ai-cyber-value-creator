---
name: define-icp
description: >
  Guide the user to a precise Ideal Customer Profile (ICP). Start from the four
  eternal niches (health, wealth, relationships, happiness), elicit who they
  serve, narrow to a specific avatar, then capture six ICP dimensions: location,
  onsite/virtual, company size, role, experience level, and industry. Use during
  the Create Value foundation, step 1 (ICP).
metadata:
  tags: [icp, niche, gtm, discovery, cyber-value-creator]
  always_load: false
---

# Define the ICP

Run this conversation with the user to produce ONE precise Ideal Customer Profile.
Be directive and deterministic: ask the questions in order, do not skip steps, do
not invent the answers, and do not advance until the user confirms each gate.
When finished, record the result with the `record_company_context` tool
(field: `icp`).

> Style: elicit, don't assume. Ask one focused question at a time, reflect the
> answer back, then proceed. If the user is vague, offer 2–3 concrete options to
> react to rather than asking them to produce an answer cold.

---

## Step 0 — The opening question (always ask this first, verbatim)

> **"Who are you trying to serve?"**

Let them answer freely. Capture it. Do not correct or narrow yet — Step 1 places it.

## Step 1 — Anchor to an eternal niche

Every durable market ladders up to one of four **eternal niches** — people always
want more of these and pay for them:

1. **Health** — body, energy, longevity, looks, mental health.
2. **Wealth** — making money, saving time, careers, business growth.
3. **Relationships** — dating, marriage, family, community, network.
4. **Happiness** — meaning, peace of mind, status, identity, fun.

From the user's Step 0 answer, identify which eternal niche it serves and say so
explicitly: *"That lives in the **{niche}** niche — the deep, durable demand
you're tapping."* If the answer spans more than one, ask the user to pick the
**primary** one (the dominant promise). Do not proceed with more than one primary
niche.

If the user doesn't know who they serve, ask: *"Which of these four do you most
want to help people with — their health, their wealth, their relationships, or
their happiness?"* Then work down from there.

## Step 2 — Narrow the niche to a specific avatar

A niche is not an ICP. Narrow in three moves; confirm each before the next:

1. **Niche → sub-niche.** *"Within {niche}, what specific outcome do you help
   with?"* (e.g. Wealth → "help service businesses get more clients with AI").
2. **Sub-niche → who specifically.** *"Who specifically has that problem and can
   pay to solve it?"* Push for a person, not a category.
3. **Avatar → recognizable.** *"If I walked into a room, how would I spot your
   ideal customer? What do they call themselves?"*

Rule of thumb: a good ICP is **specific enough that the customer says "that's me."**
Narrower converts better than broad — reassure the user that niching down does not
shrink the opportunity, it sharpens the message.

## Step 3 — Capture the six ICP dimensions

Now make it concrete. Elicit each dimension below in order. For each: ask the
question, offer the example/options if the user stalls, and record their answer.
"N/A" is a valid answer for a dimension that doesn't apply (e.g. Industry for a
consumer offer) — note it explicitly rather than leaving it blank.

| # | Dimension | Ask | Examples / options to offer |
|---|-----------|-----|------------------------------|
| 1 | **Location** | "Where are they — local, a region, or anywhere?" | "Anywhere, globally" · a country · a metro |
| 2 | **Onsite / Virtual** | "Do you serve them in person, virtually, or both?" | "Virtual only" · onsite · hybrid |
| 3 | **Company size** | "How big is their company/team (if B2B)?" | "1–5 people (solo/small)" · 5–50 · 50–500 · enterprise · N/A (consumer) |
| 4 | **Role** | "Who exactly do you sell to — their job title / role?" | "Founder" · CEO · CIO · Head of Marketing · the individual |
| 5 | **Experience level** | "How experienced are they at solving this themselves?" | "Less / beginner" · intermediate · expert |
| 6 | **Industry** | "Any specific industry — or any industry, with strength in some?" | "Any industry, strong in Healthcare, Finance, Manufacturing" · a single vertical · N/A |

Example of a completed ICP Analysis (an AI-consulting ICP):
> Location: Anywhere, globally · Onsite/Virtual: Virtual only · Company size:
> Smaller to medium, 1–5 people · Role: Founder · Experience level: Less ·
> Industry: Any industry (strong in Healthcare, Finance, Manufacturing).

## Step 4 — Synthesize + confirm (the gate)

Write a one-paragraph ICP statement in this exact shape and read it back:

> **ICP:** {role} at {company size} {industry} companies, {location}, served
> {onsite/virtual}, who are {experience level} at {the outcome}. They live in the
> **{eternal niche}** niche. You recognize them because {recognition signal}.

Then ask: *"Is this exactly who you want to serve? Anything to sharpen?"* Iterate
until the user says yes. **Do not finish without an explicit confirmation.**

## Step 5 — Record it (always do this)

Call the `record_company_context` tool with:
- `field`: `icp`
- `content`: the confirmed ICP statement plus the six-dimension table.

This makes the ICP the shared source of truth every agent reads. The next
foundation step (Understand Their Problems) builds directly on it.
