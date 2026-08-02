"""AI Cyber Value Creator — methodology data model.

The flywheel: four phases traversed clockwise (Attract → Nurture → Convert →
Deliver, looping back to Attract), preceded by the linear "Create Value"
foundation (ICP → Problems → Solutions → Offer → Elevator Pitch).

Each phase has a target metric (``goal``) and an ordered list of sub-tasks.
``gate_to_next`` is the overlap zone you pass through on the way to the next
phase (Leads → Trust → Sales → Testimonials).
"""

from __future__ import annotations

from dataclasses import dataclass, field

PLUGIN_ID = "ai-cyber-value-creator"
PLUGIN_VERSION = "1.0.0"

CENTER_LABEL = "AI Cyber Value Creator"
CONTEXT_FILE_NAME = "company-context.md"
PLAYBOOK_SKILL_SLUG = "ai-cyber-value-creator-playbook"
CONTEXT_SKILL_SLUG = "company-context"

# Ordered fields of the company context — match the Create Value foundation.
CONTEXT_FIELDS = [
    {"key": "icp", "label": "Ideal Customer Profile (ICP)", "hint": "Who we serve"},
    {"key": "problems", "label": "Their Problems", "hint": "The painful, urgent problems we solve"},
    {"key": "solutions", "label": "Candidate Solutions", "hint": "Solutions / Video-Ad topics for those problems"},
    {"key": "offer", "label": "Active Offer", "hint": "The one offer we are currently delivering"},
]
CONTEXT_FIELD_KEYS = [f["key"] for f in CONTEXT_FIELDS]

ELEVATOR_PITCH_KEY = "elevatorPitch"
ELEVATOR_PITCH_LABEL = "Elevator Pitch"
ELEVATOR_PITCH_HINT = "One line — the final foundation step"

# Skill files this plugin ships (skills/<slug>/SKILL.md), registered as
# "ai-cyber-value-creator:<slug>".
FILE_SKILLS = [
    {"slug": PLAYBOOK_SKILL_SLUG, "name": "AI Cyber Value Creator Playbook"},
    {"slug": "define-icp", "name": "Define ICP"},
    {"slug": "research-problems", "name": "Understand Their Problems"},
    {"slug": "build-solutions", "name": "Build Solutions"},
    {"slug": "craft-offer", "name": "Make Offers — Grand Slam Offer"},
    {"slug": "craft-elevator-pitch", "name": "Craft the Elevator Pitch"},
    {"slug": CONTEXT_SKILL_SLUG, "name": "Company Context"},
]

STATUS_ORDER = ["todo", "in-progress", "done"]

# The guidance skill each foundation step leans on (loaded into the kanban
# worker via the task's skills list).
STEP_SKILLS = {
    "create-value-icp": "define-icp",
    "create-value-problems": "research-problems",
    "create-value-solutions": "build-solutions",
    "create-value-offers": "craft-offer",
    "create-value-pitch": "craft-elevator-pitch",
}

# The company-context field each foundation interview locks in — a step
# reset must clear exactly this field (and no other step's) so the fresh
# worker re-asks from the top instead of reading the old answers back.
STEP_CONTEXT_KEYS = {
    "create-value-icp": "icp",
    "create-value-problems": "problems",
    "create-value-solutions": "solutions",
    "create-value-offers": "offer",
    "create-value-pitch": ELEVATOR_PITCH_KEY,
}


@dataclass(frozen=True)
class TaskDef:
    id: str
    title: str
    blurb: str
    brief: str | None = None


@dataclass(frozen=True)
class PhaseDef:
    id: str
    name: str
    color: str
    goal: str
    gate_to_next: str
    tasks: tuple[TaskDef, ...]
    foundation: bool = False


VALUE_CREATION_PHASE = PhaseDef(
    id="create-value",
    name="Create Value",
    color="#14b8a6",
    goal="A validated, packaged first offer",
    gate_to_next="Offer",
    foundation=True,
    tasks=(
        TaskDef(
            id="create-value-icp",
            title="Get Clarity on the ICP",
            blurb="Pin down exactly who you serve before anything else.",
            brief=(
                "Use the `ai-cyber-value-creator:define-icp` skill — it is the step-by-step method "
                "(start from the eternal niches: health, wealth, relationships, happiness, with the "
                'opening question "Who are you trying to serve?"). Determine the Ideal Customer '
                "Profile TOGETHER WITH the user: niche → avatar → the six dimensions (location, "
                "onsite/virtual, company size, role, experience level, industry). Do not finish "
                "until the user explicitly confirms the ICP — every later task builds on it. Once "
                "confirmed, record it with the `record_company_context` tool (field: icp) so every "
                "future session knows who we serve."
            ),
        ),
        TaskDef(
            id="create-value-problems",
            title="Understand Their Problems",
            blurb="Research the ICP's real, painful, urgent problems.",
            brief=(
                "Use the `ai-cyber-value-creator:research-problems` skill. Using internet research "
                "and deep analysis of the confirmed ICP, produce a prioritized list of their real, "
                "painful, urgent problems (score each: severity × frequency × urgency). Cite "
                "findings/sources. **Capture the COMPLETE list — every problem, in priority order, "
                "each with its score** (they also become video/ad topics and feed future offers). "
                "Confirm the LIST with the user (complete? correctly ordered?) — do NOT make them "
                "pick a single problem here; necking down to one (or a couple combined) happens at "
                "the solution/offer steps. Record the WHOLE ordered list (write `company-context.md` "
                "under `## Their Problems`; also use the `record_company_context` tool, field: problems)."
            ),
        ),
        TaskDef(
            id="create-value-solutions",
            title="Build Solutions",
            blurb="Turn the validated problems into candidate solutions (and Video/Ad topics).",
            brief=(
                "Use the `ai-cyber-value-creator:build-solutions` skill. Working down the FULL "
                "prioritized problem list, generate candidate solutions (mechanisms that deliver the "
                "dream outcome) — at least one per top problem. For each: what it is, which problem "
                "it solves, format/delivery, and why it fits the ICP. These double as Video/Ad topic "
                "ideas, so capture them ALL, ranked. Do NOT pick the single offer here — that's the "
                "next step. Record the whole ranked list (write `company-context.md` under "
                "`## Candidate Solutions`; also use `record_company_context`, field: solutions)."
            ),
        ),
        TaskDef(
            id="create-value-offers",
            title="Make Offers",
            blurb="Package one One-Page Offer to start; save the rest for later.",
            brief=(
                "Use the `ai-cyber-value-creator:craft-offer` skill (Hormozi $100M Offers: the value "
                "equation + the Current→End-State bridge + the Grand Slam stack). This is where we "
                "NECK DOWN: from the full problem + solution lists, help the user pick ONE "
                "problem/solution to start with (or a couple combined into one offer if it genuinely "
                "makes sense) and package it as a One-Page Offer. Then ASK the user which (if any) of "
                "the remaining solutions to SAVE for later, and append ONLY the ones they choose to "
                "`saved-offers.md` in the workspace so those future offers are registered and "
                "remembered. Never auto-save solutions the user did not pick. Record the active offer "
                "with the `record_company_context` tool (field: offer) so every future session knows "
                "what we are delivering. Then the final step is to craft the elevator pitch."
            ),
        ),
        TaskDef(
            id="create-value-pitch",
            title="Craft the Elevator Pitch",
            blurb="Distill the whole foundation into one line.",
            brief=(
                "Use the `ai-cyber-value-creator:craft-elevator-pitch` skill. Using the FULL company "
                "context (ICP, problems, solutions, the active offer, AND the confirmed niche / "
                "outcome / avatar / recognition signal — read all of company-context.md, not just "
                "the headline fields), write ONE elevator pitch in EXACTLY this shape: "
                '"I help [brief ICP name] with [problem] [achieve outcome] within [timeframe]." '
                "A single plain sentence — a short human ICP name (not the full profile), the core "
                "problem, the outcome, and a realistic timeframe drawn from the offer. Show it to "
                "the user and refine until they're happy, then record it by writing "
                "`company-context.md` under the `## Elevator Pitch` section (also use the "
                "`record_company_context` tool, field: elevatorPitch). Completing this task lays "
                "the foundation to enter the flywheel laps."
            ),
        ),
    ),
)

ROADMAP_PHASES: tuple[PhaseDef, ...] = (
    PhaseDef(
        id="attract",
        name="Attract",
        color="#ec4899",
        goal="Leads × day",
        gate_to_next="Leads",
        tasks=(
            TaskDef(
                id="attract-referral",
                title="Build High-Trust Referral Network",
                blurb="Cultivate partners and champions who send warm, pre-trusted leads.",
            ),
            TaskDef(
                id="attract-tribe",
                title="Lead Your Tribe: Build Solutions",
                blurb="Define the audience you lead and the problems you uniquely solve for them.",
            ),
            TaskDef(
                id="attract-shortform",
                title="Short-Form Content + Ads",
                blurb="Run short-form content and paid ads to put leads on the board every day.",
            ),
        ),
    ),
    PhaseDef(
        id="nurture",
        name="Nurture",
        color="#f59e0b",
        goal="Customers × week (low ticket)",
        gate_to_next="Trust",
        tasks=(
            TaskDef(
                id="nurture-community",
                title="Build a Community",
                blurb="Build an engaged Skool community that fosters real engagement and belonging.",
            ),
            TaskDef(
                id="nurture-longform",
                title="Long-Form Watering-Hole Content",
                blurb="Publish deep long-form content where your audience already gathers.",
            ),
            TaskDef(
                id="nurture-funnel",
                title="Streamline Sales: Funnel Automations (GHL + Skoot)",
                blurb="Automate the nurture-to-buy funnel with GHL + Skoot so it runs itself.",
            ),
        ),
    ),
    PhaseDef(
        id="convert",
        name="Convert",
        color="#22c55e",
        goal="Clients × month (high ticket)",
        gate_to_next="Sales",
        tasks=(
            TaskDef(
                id="convert-nopressure",
                title="No-Pressure Sales — Zoom, Sell by Chat, Conversion Events",
                blurb="Convert with low-pressure Zoom calls, chat selling, and conversion events.",
            ),
            TaskDef(
                id="convert-scarcity",
                title="Build Scarcity + Wait List + Applications",
                blurb="Use a wait list and applications to create real scarcity and qualify buyers.",
            ),
            TaskDef(
                id="convert-campaigns",
                title="Sales Campaigns — Scheduled for Months",
                blurb="Plan and schedule recurring sales campaigns months in advance.",
            ),
        ),
    ),
    PhaseDef(
        id="deliver",
        name="Deliver",
        color="#3b82f6",
        goal="High Retention",
        gate_to_next="Testimonials",
        tasks=(
            TaskDef(
                id="deliver-journey",
                title="Design & Share Client Journey (Long Term)",
                blurb="Map and communicate the long-term client journey so wins compound.",
            ),
            TaskDef(
                id="deliver-systemize",
                title="Systemize + Productize Service Delivery",
                blurb="Turn delivery into a repeatable, productized system that scales.",
            ),
            TaskDef(
                id="deliver-choreograph",
                title="Choreograph Client Experience",
                blurb="Choreograph every touchpoint so the experience earns referrals + testimonials.",
            ),
        ),
    ),
)

# Foundation first, then the four flywheel phases (task lookup + roadmap order).
ALL_PHASES: tuple[PhaseDef, ...] = (VALUE_CREATION_PHASE, *ROADMAP_PHASES)
ALL_TASK_IDS: list[str] = [t.id for p in ALL_PHASES for t in p.tasks]


def phase_def(phase_id: str) -> PhaseDef | None:
    for p in ALL_PHASES:
        if p.id == phase_id:
            return p
    return None


def phase_for_task(task_id: str) -> tuple[PhaseDef, TaskDef] | None:
    for phase in ALL_PHASES:
        for task in phase.tasks:
            if task.id == task_id:
                return phase, task
    return None


def step_task_title(phase: PhaseDef, task: TaskDef) -> str:
    """Deterministic kanban-task title for a roadmap step (used for link
    rediscovery, same rule as the paperclip original's issue titles)."""
    return f"{phase.name}: {task.title}"


def next_status(status: str) -> str:
    try:
        i = STATUS_ORDER.index(status)
    except ValueError:
        i = -1
    return STATUS_ORDER[(i + 1) % len(STATUS_ORDER)]


# ---------------------------------------------------------------------------
# Task briefs — the executive brief attached to every step's kanban task.
# Foundation steps run DIRECTLY with the user; flywheel steps are execution
# work the agent may decompose. Ported from the paperclip worker, with the
# paperclip control-plane mechanics replaced by hermes-native equivalents.
# ---------------------------------------------------------------------------

def build_task_description(
    phase: PhaseDef, task: TaskDef, *, context_dir: str | None = None
) -> str:
    header = [
        f"## {phase.name} → {task.title}",
        "",
        "This task is part of the **AI Cyber Value Creator** playbook.",
        f"**Phase:** {phase.name} (goal: {phase.goal})",
        f"**Step:** {task.title}",
        f"**Intent:** {task.blurb}",
        "",
        f"Load and follow the `ai-cyber-value-creator:{PLAYBOOK_SKILL_SLUG}` skill — it is the",
        "master method for this work (foundation → flywheel, the order of operations, and the",
        "tactics). Also load `ai-cyber-value-creator:company-context` and read the shared",
        "Company Context before acting.",
        "",
    ]
    if context_dir:
        header += [
            f"The shared Company Context lives at `{context_dir}/{CONTEXT_FILE_NAME}` —",
            "read it before acting and keep it current as facts are confirmed.",
            "",
        ]

    generic = [
        "### You are the executive for this step. Work in this exact order:",
        "",
        "1. **Search the available skills FIRST.** Enumerate the skills installed in",
        "   this system and identify which ones can accomplish (or partially",
        "   accomplish) this step. Do not invent an approach before checking what",
        "   skills already exist.",
        "2. **Clarify scope BEFORE acting.** Based on what the skills can do and what",
        "   this step needs, state the scope, target audience, offer, constraints, and",
        "   definition of done — and surface any open questions for the user in your",
        "   first status update rather than guessing.",
        "3. **Execute methodically.** Work the step with the chosen skill(s) and the",
        "   clarified requirements, breaking it into sub-pieces if needed.",
        "4. **Report & close.** When the work is done, summarize the outcome, save",
        "   deliverables in the workspace, and complete this task.",
    ]

    foundation_brief = [
        "### How to run this step",
        task.brief or task.blurb,
        "",
        "**Answer-first (ask) mode.** This is a question-and-answer step, not an",
        "execution task: the goal is to reach the answer *with the user*, fast. Do",
        "NOT write implementation code, and do NOT produce an implementation plan or",
        "roadmap for it. Use tools only for investigation or scratch work. The",
        "deliverable is the user-confirmed answer recorded into the shared Company",
        "Context (step 3 below) — that recorded answer IS the output. Don't spin up a",
        "full execution workflow; just talk, synthesize, confirm, record.",
        "",
        "**You run this step yourself, directly with the user.** This is",
        "foundational strategy (who we serve, what we deliver): an interview, not a",
        "deliverable to delegate. Work in this order:",
        "",
        "1. **Load the named guidance skill above** (and search for any others that",
        "   help). It is the precise method for this step.",
        "2. **Talk with the user.** Group the related questions together (e.g. ask the",
        "   remaining ICP dimensions — company size, role, experience, industry — in",
        "   one message) to minimise slow round-trips. Never re-ask a question that's",
        "   already answered — re-read the conversation first. Don't produce the final",
        "   output until the user has answered and confirmed.",
        "3. **Record the result** into the shared Company Context using the",
        "   `record_company_context` tool (it writes `company-context.md` — sections:",
        "   ## Ideal Customer Profile, ## Their Problems, ## Candidate Solutions,",
        "   ## Active Offer) — that record is what every future session reads.",
        "",
        "**Keep going until the step is actually finished.** This is a live",
        "conversation: after the user answers, immediately continue (ask the next",
        "question, or synthesize and confirm) — do NOT idle waiting on yourself. The",
        "only valid resting states are: blocked with an open question the user still",
        "has to answer, or done once the answer is confirmed AND recorded via",
        "`record_company_context`.",
        "",
        "**HOW TO ASK THE USER (question-card protocol — MANDATORY).** The user",
        "answers from the Value Creator roadmap page, which renders your question as",
        "a card. To ask:",
        "1. Post ONE kanban comment whose FIRST line is exactly:",
        "   `### ❓ QUESTION FOR YOU`",
        "   followed by the question(s) in markdown — group every related",
        "   question into this single comment. When the answer is a choice",
        "   between discrete options, list each option on its own line starting",
        "   with '- ' (the dashboards render those lines as clickable answer",
        "   buttons).",
        "2. THEN block the task with kind `needs_input` and a reason that STARTS",
        "   with a unique question tag, e.g. 'Q3 (company size): waiting for your",
        "   answer — see the question card.' The tag MUST differ for every",
        "   question (the board treats repeated identical block reasons as a",
        "   stuck loop and pulls the task away). Never put the question itself",
        "   only in the block reason, and never block without having posted the",
        "   question comment first.",
        "3. When you resume, the user's answer is in the newest comments — read",
        "   them FIRST, acknowledge, and continue. Never re-post an answered",
        "   question.",
        "",
        "**Before you EVER mark this task blocked, re-read the conversation.** The",
        "user may have answered already. If every question you asked is answered, do",
        "NOT block — continue (ask the next grouped question, or synthesize + confirm",
        "+ record + complete). Only block when there is a genuinely unanswered",
        "question currently open.",
        "",
        "**Do NOT delegate ANY part of a foundation step — not even research.** YOU",
        "both talk to the user and do the work yourself the whole way through,",
        "including any web research or analysis. Never create subtasks, never hand",
        "off the conversation. The foundation is a direct executive ↔ user",
        "conversation from start to finish.",
        "",
        '**This instruction OVERRIDES any standing "always delegate / orchestrate,',
        'don\'t execute" guidance** — from any skill, memory, or other plugin. For',
        "THIS foundation step, do the work yourself.",
    ]

    if phase.foundation:
        specific = foundation_brief
    elif task.brief:
        specific = [
            "### How to run this step",
            task.brief,
            "",
            "Run it the AI Cyber Value Creator way: **search the available skills FIRST**,",
            "**clarify scope and surface open questions BEFORE acting**, then execute",
            "methodically. Update the roadmap step and complete this task when the",
            "step is done.",
        ]
    else:
        specific = generic

    deliverable = [
        "",
        "### Save the deliverable in the workspace (required)",
        "Whatever user-inspectable deliverable this step produces — the One-Page",
        "Offer, an ICP profile, a ranked problem/solution list, the elevator pitch, a",
        "content piece, a funnel doc, a campaign plan, a report — **must be saved as",
        "a file in the workspace** and named in your final summary so the user can",
        f"find it. Recording into `{CONTEXT_FILE_NAME}` is internal context and does",
        "NOT count as the deliverable.",
        "",
        "**Do not complete this task until the deliverable file exists.**",
    ]

    return "\n".join([*header, *specific, *deliverable])
