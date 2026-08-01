---
name: craft-offer
description: >
  Package ONE chosen solution into a Grand Slam Offer (Hormozi $100M Offers
  method) as a One-Page Offer, create it as the active project, and save the rest
  as future-offer drafts only if the user picks them. Use during the Create Value
  foundation, step 4 (Make Offers), after solutions are confirmed.
metadata:
  tags: [offer, hormozi, grand-slam-offer, pricing, cyber-value-creator]
  always_load: false
---

# Make Offers — Grand Slam Offer (Hormozi style)

Help the user pick ONE solution and turn it into an irresistible **Grand Slam
Offer** — "so good people feel stupid saying no" — packaged as a One-Page Offer.
Method: Alex Hormozi's `$100M Offers`. Be directive and deterministic. When
finished, create the active offer as a project, save chosen runner-ups as drafts,
and call `record_company_context` (field: `offer`).

> Prerequisite: the ranked solutions must be confirmed (see `build-solutions` /
> the Company Context `solutions` field). If not, complete that first.

---

## Step 1 — Neck down to the first offer

Recall the ICP, the **full** ranked problem list, and the ranked solutions. This is
where we narrow: help the user choose **one** problem/solution to start with
(highest demand × differentiation × deliverability) — **or a couple combined into a
single offer if they genuinely belong together** (e.g. one problem whose fix
naturally bundles two solutions). Confirm the pick before building. Build **one
offer** now — do not build several separate offers at once; the rest of the
problems and solutions stay captured for future offers and video/ad topics.

> **Steps 2–4 are your INTERNAL analysis — never shown to the client.** The
> framework names below (Value Equation, Dream Outcome, Probability, Bridge /
> Current State → End State, Value Stack, MAGIC) are *how you think*, not words
> the customer ever reads. They must NOT appear in the One-Page Offer (Step 5)
> or its PDF. The client document is plain, compelling, benefit-language copy.

## Step 2 — Anchor on the Hormozi Value Equation (internal)

Everything in the offer moves these four levers:

> **Value = (Dream Outcome × Probability of Achieving) ÷ (Time × Effort to Achieve)**

- **Maximize** the **Dream Outcome** (the result they truly want) and the
  **Probability of Achieving** it (proof, guarantees, track record, a clear path).
- **Minimize** the **Time** to achieve it (how fast they see results) and the
  **Effort** to achieve it (how hard/annoying it is for them).

Evaluate the chosen solution against each of the four levers and note exactly how
the offer will push each one. A great offer wins on all four.

## Step 3 — Frame the Bridge (Current State → End State) (internal)

Position the offer as the **bridge** that carries the customer from where they are
to where they want to be. Capture both ends explicitly:

- **A — Current State (their frustrations).** Where they are today and what's
  painful about it — pulled from the validated problems, in their own words.
- **B — End State (their goals / desired outcomes).** Where they want to be —
  framed as **outcomes, NOT tools and NOT processes.** People buy the destination
  (the result / the new identity), not the mechanism. Describe what their life or
  business looks like once they've arrived.

The **offer is the "How"** — the bridge from A to B. Every deliverable in the
stack below must visibly help the customer cross A → B; if it doesn't, cut it.
Keep all messaging on **B (outcomes)** — the tools and processes are *how you
deliver*, never *what you sell*.

## Step 4 — Build the offer (the Grand Slam stack) (internal)

Work these in order; capture each:

1. **Dream outcome** — the specific, vivid result (tie to the ICP's #1 problem).
2. **List every problem** on the path to that outcome (obstacles the customer hits).
3. **Turn each problem into a solution/deliverable** — what you provide to remove it.
4. **Trim & stack** — keep the deliverables with high value and low delivery cost;
   cut high-cost/low-value ones. Present the kept ones as a stacked **value list**
   (each with an honest standalone price) so the total dwarfs the ask.
5. **Enhance perceived likelihood** — add proof: results, testimonials, case
   studies, a clear step-by-step path.
6. **Reduce time delay** — show fast "first win"; sequence quick wins early.
7. **Reduce effort & sacrifice** — done-for-you/done-with-you elements, templates,
   onboarding.
8. **Guarantee** — pick a strong, specific guarantee (unconditional, conditional/
   "do the work", or a results/"keep-the-bonuses" guarantee). Reverse the risk.
9. **Scarcity & urgency** — real limits (cohort size, wait list, deadline, bonus
   expiry). Never fake them.
10. **Bonuses** — stack 2–4 bonuses that solve adjacent problems; name each with
    its value and the specific objection it kills.
11. **Name it (MAGIC)** — a compelling name signaling Magnetic reason-why,
    Avatar, Goal, Interval/time, Container (e.g. "The 90-Day AI Value Sprint").
12. **Price** — anchor against the stacked value and the dream-outcome's worth
    (value-based, not cost-plus). State the price and the value-to-price ratio.

## Step 5 — Produce the One-Page Offer (CLIENT-FACING)

Now turn the internal analysis into a **client-facing** one-pager — the document
a prospect reads and feels they'd be stupid to say no to. Write it as marketing
copy, not a framework worksheet. **Strip ALL internal jargon:** no "dream
outcome", "value equation", "probability", "current state / end state",
"bridge", "value stack", "MAGIC", "levers", "perceived likelihood". The customer
sees benefits and the transformation, never the machinery.

Voice: confident, concrete, second-person ("you"), outcome-first. Use the
customer's own language for their problem. Every line earns its place.

Structure the markdown like this (adapt headings to sound natural, keep the
order):

```
# {Offer name}
### {One-line promise — the result, in plain words}

**Who this is for:** {the ICP in their own words, one or two sentences}

**What this does for you:** {2–4 sentences painting the after-state as outcomes
— what becomes true for them, no tools/process talk}

## What's included
- **{Inclusion name}** — {the benefit it delivers to you} *(value: ${X})*
- ... (each kept deliverable as a benefit line with an honest standalone value)

**Total value: ${stacked total}**

## Bonuses
- **{Bonus name}** — {benefit; the worry it removes} *(value: ${X})*

## Our guarantee
{the risk reversal in plain, reassuring language}

## Availability
{the real scarcity / urgency — cohort size, deadline, etc.}

## Your investment
**${price}** — for everything above (a ${stacked total} value).
{one compelling line on why it's a smart yes.}

## Next step
{the single clear call to action}
```

Read it back and confirm with the user. **Do not finish without confirmation.**
Refine the copy until it lands.

## Step 6 — Create the active offer + save the rest

1. **Record the chosen offer as the ACTIVE offer** (this is what the
   company is now delivering) — record it with the `record_company_context`
   tool (field: offer) and write it into `company-context.md` under
   `## Active Offer`.
2. **Ask the user which (if any) of the remaining solutions to SAVE for later.**
   For ONLY the ones they choose, append them to a `saved-offers.md` file in the
   workspace so those future offers are registered and remembered. **Never
   auto-save solutions the user did not pick.**

## Step 7 — Publish the One-Page Offer as deliverables: markdown + dark-theme PDF (required)

The One-Page Offer is the company's flagship client-facing deliverable, so it
must be produced in **BOTH formats** — a markdown source and a polished,
dark-theme PDF the user can send to a prospect as-is.

1. **Markdown.** Write the confirmed client-facing one-pager (Step 5, jargon
   stripped) to `one-page-offer.md` in the workspace.
2. **Dark-theme PDF — one page, edge-to-edge, designed.** Render
   `one-page-offer.pdf`. It must be **a single page**, **full-bleed dark** (NO
   white border/margins), and look like a designed sales asset — not a memo.

   **Render it with whatever markdown→PDF tool is available** (a make-pdf skill,
   `pandoc` + a headless-Chromium print, or any equivalent). Whatever the tool,
   configure it for **zero page margins and no header/footer/page-number chrome**
   — a white border, running header, or page number ruins a designed page.

   **Dark theme + full-bleed (prepend this `<style>` to the markdown):**
   ```html
   <style>
   * { -webkit-print-color-adjust: exact; print-color-adjust: exact; box-sizing: border-box; }
   @page { size: letter; margin: 0; }
   html, body { margin: 0; padding: 0; background: #0b0b14 !important; }
   /* body padding insets the content; the bg fills the whole page (full-bleed) */
   body { padding: 0.5in 0.6in; font-family: -apple-system, Helvetica, Arial, sans-serif;
          line-height: 1.34; color: #e8e8f2; font-size: 11px; }
   h1 { color: #fff; font-size: 24px; margin: 0 0 4px; line-height: 1.08; }
   h3 { color: #2dd4bf; font-weight: 600; font-size: 14px; margin: 0 0 13px; }
   h2 { color: #2dd4bf; font-size: 11px; letter-spacing: .06em; text-transform: uppercase;
        border-bottom: 1px solid #2b3050; padding-bottom: 3px; margin: 13px 0 6px; }
   p  { font-size: 11px; margin: 0 0 6px; color: #e8e8f2; }
   ul { margin: 4px 0; padding-left: 18px; }
   li { font-size: 11px; margin: 0 0 5px; color: #e8e8f2; }
   strong { color: #fff; }
   </style>
   ```
   The `font-size: 11px` here is a STARTING point — raise it (12, 13, …) until the
   page is full (see the fill rule below); drop it / go two-column only if it
   spills to a second page.
   Inset the content with **body padding** (e.g. `body { padding: 0.5in 0.6in }`)
   rather than a wrapper `<div>` — markdown inside a raw `<div>` may not be
   parsed. Keep `print-color-adjust: exact`, `@page margin: 0`, and a full-page
   background. **Set an explicit light color on every text element** (`body, p,
   li, h2, strong` …) — most markdown→PDF default stylesheets use dark text, which is
   invisible on a dark background if you only color the headings.

   **Exactly ONE page, and it must FILL the page.** Two-sided requirement:
   - If it spills onto a 2nd page → tighten (smaller font, two-column
     `What's included`/`Bonuses` via `columns: 2`, trim the longest paragraph,
     reduce margins) until it's one page.
   - If the content stops partway and the **bottom of the page is empty** →
     **increase the base font size (and spacing) until the content fills ~90–100%
     of the page height.** A one-pager with the bottom third blank is wrong; bump
     the font up step by step until it fills, then back off only if it overflows.
   The goal is the **largest font that still fits on exactly one page** with the
   page comfortably full. Iterate by previewing the rendered HTML/PDF and re-checking the
   page count after each change. **Do not
   stop at a 2-page, white-bordered, or half-empty PDF.**
3. **Save both deliverables in the workspace** (`one-page-offer.md` and
   `one-page-offer.pdf`) and name both files in your final summary so the
   user can find them.

The client document and PDF contain **zero** internal framework terms (see Step
5). **Do not mark the task done until both the markdown file and the
dark-theme PDF exist in the workspace.**

## Step 8 — Record it into the Company Context (always do this)

Call `record_company_context` with:
- `field`: `offer`
- `content`: the client-facing One-Page Offer (offer name, who it's for, the
  transformation, what's included with values, bonuses, guarantee, availability,
  price) for the active offer — the same jargon-free copy as the artifact.

This is what every agent will read as "what we are delivering." Completing this
lays the foundation to enter the flywheel laps.
