"""In-page roadmap coach — per-step streaming interviews (no kanban, no
worker sessions).

Each roadmap item gets its own persisted conversation with the Coach (the
mentee's connected LLM via the host-owned PluginLlm facade — same pattern as
the value-creator-level Examiner). Foundation steps interview toward their
company-context field and record it on completion; flywheel steps coach the
mentee through implementation with detailed guidance and store a completion
summary. Conversations, statuses, and summaries persist server-side; every
step can be reset independently.
"""
from __future__ import annotations

import json
import re
import threading
import time
from typing import Any, Optional

from . import context_store, progress
from .methodology import (
    ALL_PHASES,
    STEP_CONTEXT_KEYS,
    phase_for_task,
)

PLUGIN_ID = "ai-cyber-value-creator"
MIN_TURNS = 2          # never conclude before the mentee has answered twice
MAX_TURNS = 14         # a working session, not an interrogation

_LOCK = threading.Lock()

# ---------------------------------------------------------------------------
# Guidance — shown on the page as bullets AND injected into the Coach's
# system prompt. Foundation steps summarize their skill's method; flywheel
# steps get the detailed implementation guidance the kanban briefs never had.
# ---------------------------------------------------------------------------

GUIDANCE: dict[str, list[str]] = {
    # ---- Create Value foundation ------------------------------------------
    "create-value-icp": [
        "Start from the eternal niches — health, wealth, relationships, happiness — and ask: who are you trying to serve?",
        "Neck down: niche → avatar → the six dimensions (location, onsite/virtual, company size, role, experience level, industry).",
        "Test it: could you recognize this person in a crowded room? If not, it's still too broad.",
        "The confirmed ICP is recorded to Company Context — every later step builds on it.",
    ],
    "create-value-problems": [
        "Research the ICP's real, painful, urgent problems — not what you assume, what they actually say.",
        "Score each problem: severity × frequency × urgency, and keep the COMPLETE prioritized list.",
        "These problems double as your video and ad topics later — none of them are wasted.",
        "Don't pick one yet — necking down to a single problem happens at the offer step.",
    ],
    "create-value-solutions": [
        "For each top problem, design at least one mechanism that delivers the dream outcome.",
        "For each solution: what it is, which problem it solves, format/delivery, why it fits the ICP.",
        "Rank them all — they double as Video/Ad topic ideas for the Attract phase.",
        "Still no picking — the single offer decision is the next step.",
    ],
    "create-value-offers": [
        "This is where you neck down: ONE problem + solution packaged as a One-Page Offer.",
        "Use the Hormozi value equation: dream outcome × likelihood ÷ (time delay × effort).",
        "Build the Grand Slam stack: core offer, bonuses, guarantee, scarcity, urgency, name.",
        "Choose which remaining solutions to save for later — only the ones you pick get saved.",
    ],
    "create-value-pitch": [
        "One sentence, exactly this shape: \"I help [ICP] with [problem] [achieve outcome] within [timeframe].\"",
        "Short human ICP name — not the full profile. Realistic timeframe drawn from the offer.",
        "Say it out loud. If you stumble, it's too long.",
        "Completing this unlocks the flywheel laps below.",
    ],
    # ---- Attract -----------------------------------------------------------
    "attract-referral": [
        "List every person who already trusts you and touches your ICP: past clients, peers, vendors, communities.",
        "Give first: send them leads, content, or intros before you ever ask for one.",
        "Make referring easy: a one-line description of who you help (your elevator pitch) plus a simple way to intro you.",
        "Set a cadence — a weekly touch with 3-5 partners beats a yearly blast to fifty.",
        "Track where every warm lead comes from so you know which relationships to invest in.",
    ],
    "attract-tribe": [
        "Decide what tribe you LEAD — not just sell to: the transformation you stand for.",
        "Plant a flag: a clear, repeatable point of view that attracts your ICP and repels everyone else.",
        "Show up where the tribe already is before asking them to come to you.",
        "Turn your solutions list into teaching moments — every problem you researched is content.",
        "Consistency beats brilliance: a sustainable publishing rhythm you can hold for a year.",
    ],
    "attract-shortform": [
        "Short-form (Reels/Shorts/TikTok) is the discovery engine: hooks come straight from your problems list.",
        "One video = one problem = one takeaway. Resist teaching everything at once.",
        "Batch production: script and record a week at a time; repurpose across platforms.",
        "Paid ads amplify what already works organically — never cold-start an unproven message with money.",
        "Measure leads per day, not likes; every video ends with one clear next step.",
    ],
    # ---- Nurture -----------------------------------------------------------
    "nurture-community": [
        "Default path: build your OWN community (e.g. Skool) with one clear promise tied to your offer — you own the space, the norms, and the pipeline.",
        "Honest alternative: joining an established community where your ICP already gathers can foster relationships, deep problem discovery, and a place to share your solution.",
        "Probe which fits before committing: can they seed their own space daily, or is their ICP already concentrated somewhere active they should join first?",
        "If joining another's community: it IS less effective than owning — and be sensitive about pitching, it's not your space. Give value first, earn the right, respect the host's rules.",
        "Own-community playbook: design the first-week experience (day one, three, seven), seed engagement daily, keep the low-ticket path visible but not pushy.",
        "Either way, measure weekly active relationships, not signups.",
    ],
    "nurture-longform": [
        "Long-form (YouTube, podcast, newsletter) is where trust compounds — pick ONE watering hole your ICP already visits.",
        "Go deep on the problems from your research: the content that ranks is the content that answers.",
        "Every long-form piece feeds short-form clips — produce once, distribute five times.",
        "End every piece with the same bridge: community or low-ticket offer.",
        "Judge by customers per week influenced, not views.",
    ],
    "nurture-funnel": [
        "Map the full path: content → community → low-ticket → high-ticket, and automate the seams with GHL.",
        "Every lead gets tagged by source so you know which content actually sells.",
        "Automate follow-up sequences for opt-ins, purchases, and abandoned checkouts — speed to lead wins.",
        "Keep the funnel boring and reliable; creativity belongs in the content, not the plumbing.",
        "Weekly check: where do leads stall? Fix the biggest leak first.",
    ],
    # ---- Convert -----------------------------------------------------------
    "convert-nopressure": [
        "Sell the way you'd want to be sold to: diagnose, prescribe, invite — never pressure.",
        "Zoom calls: a simple agenda (their situation → the gap → your bridge → decision) keeps it honest.",
        "Sell by chat works when trust is pre-built: short questions, real listening, clear invitation.",
        "Conversion events (workshops, challenges) let one hour of you convert many at once.",
        "Every no gets a graceful path back into nurture — today's no is next quarter's yes.",
    ],
    "convert-scarcity": [
        "Real scarcity only: limited client slots because delivery is real work — never fake countdowns.",
        "A wait list turns demand into proof and gives you a warm pool for every campaign.",
        "Applications qualify buyers AND make the offer feel earned — three questions is enough.",
        "Publish your capacity honestly; sold-out months sell the next month for you.",
    ],
    "convert-campaigns": [
        "Plan campaigns quarterly: launch weeks, evergreen pushes, seasonal moments — scheduled months ahead.",
        "Each campaign has one offer, one story, one deadline; resist bundling everything.",
        "Reuse the machine: the same campaign structure re-runs with a fresh angle each time.",
        "Debrief every campaign: what to keep, kill, and double next run.",
    ],
    # ---- Deliver -----------------------------------------------------------
    "deliver-journey": [
        "Map the client journey from yes to renewal: milestones, check-ins, and the moments wins get celebrated.",
        "Share the map WITH clients — people who can see the road trust the driver.",
        "Design for the long term: what does year one look like, not just month one?",
        "Every milestone is a testimonial opportunity — build the ask into the journey.",
    ],
    "deliver-systemize": [
        "Write down how you deliver — if it only lives in your head, you are the bottleneck.",
        "Productize: same onboarding, same cadence, same deliverables — customize the content, not the container.",
        "Checklist every recurring motion; automate what repeats, delegate what's documented.",
        "Systemized delivery is what makes the next client cheaper to serve than the last.",
    ],
    "deliver-choreograph": [
        "Choreograph the experience: every touchpoint (welcome, updates, wins, renewals) designed on purpose.",
        "Surprise moments create stories clients retell — plan two per journey.",
        "Make progress visible: clients who SEE their wins renew and refer.",
        "The goal: an experience so good that referrals and testimonials are the natural exhaust.",
    ],
}


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

def _state_path():
    return context_store.get_data_dir() / "coach.json"


def load_state() -> dict:
    try:
        data = json.loads(_state_path().read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    return {"steps": {}}


def save_state(state: dict) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp.replace(path)


def _step(state: dict, task_id: str) -> dict:
    return state["steps"].setdefault(task_id, {
        "status": "open",          # open | active | complete
        "messages": [],
        "summary": "",
        "startedAt": None,
        "completedAt": None,
    })


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------

def _llm():
    from agent.plugin_llm import PluginLlm
    return PluginLlm(plugin_id=PLUGIN_ID)


def _structured(instructions: str, payload: str, schema: dict,
                temperature: float = 0.4) -> dict:
    res = _llm().complete_structured(
        instructions=instructions,
        input=[{"type": "text", "text": payload}],
        json_schema=schema,
        schema_name="coach",
        temperature=temperature,
        max_tokens=1600,
        timeout=120,
        purpose="roadmap-coach",
    )
    parsed = getattr(res, "parsed", None)
    if parsed is None:
        text = getattr(res, "text", "") or ""
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                parsed = json.loads(m.group(0))
            except json.JSONDecodeError:
                parsed = None
    if not isinstance(parsed, dict):
        raise RuntimeError("coach returned no usable JSON")
    return parsed


_TURN_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["reply", "complete"]},
        "reply": {"type": "string"},
        "summary": {"type": "string"},
        "contextValue": {"type": "string"},
    },
    "required": ["action"],
}


def _prior_knowledge(task_id: str) -> str:
    """Everything already known about this mentee beyond the company context:
    the Levels verdict and every completed roadmap step's summary — so no
    step ever starts from scratch."""
    parts = []
    lv = level_status()
    if lv["installed"] and lv["level"] > 0:
        line = f"Builder level: {lv['level']}"
        if lv.get("badge"):
            line += f" ({lv['badge']['name']})"
        if lv.get("rationale"):
            line += f". Examiner's verdict: {lv['rationale']}"
        parts.append(line)
        if lv.get("strengths"):
            parts.append("Assessed strengths: " + "; ".join(lv["strengths"]))
        if lv.get("interviewAnswers"):
            parts.append("In their level interview, in their own words, they "
                         "said: " + lv["interviewAnswers"])
        for pa in lv.get("provenActions") or []:
            parts.append("Verified done (level prescription): " + pa)
    state = load_state()
    for phase in ALL_PHASES:
        for t in phase.tasks:
            if t.id == task_id:
                continue
            st = state["steps"].get(t.id) or {}
            if st.get("status") == "complete" and st.get("summary"):
                parts.append(f"Completed step '{t.title}': {st['summary']}")
    return "\n".join(f"- {p}" for p in parts) if parts else "- (nothing yet)"


def _persona(task_id: str) -> str:
    found = phase_for_task(task_id)
    phase, task = found
    ctx_md = context_store.render_company_context_body(
        context_store.merged_context())
    bullets = "\n".join(f"- {b}" for b in GUIDANCE.get(task_id, []))
    base = (
        "You are the Roadmap Coach for the AI Cyber Value Creator program — "
        "a sharp, warm operator who works ON the business with the mentee, "
        "one step at a time, right here in this panel. One question or move "
        "per turn, always building on their answers. Be concrete: names, "
        "numbers, drafts. Push back on vague answers. Keep each reply under "
        "120 words unless drafting an artifact for them.\n"
        "YOU direct the conversation — you know the method, they don't. "
        "NEVER offer a menu of topics or ask which thing to cover next "
        "('which dimension first — location, size, or role?' is a failure). "
        "Walk the method's topics yourself, in order, one CONCRETE question "
        "at a time ('Where are these brokers — national, or specific "
        "metros?'). Offer choices only when the decision is genuinely "
        "theirs to make (e.g. picking which offer to run), never about "
        "what to discuss.\n\n"
        f"CURRENT STEP: {task.title} (phase: {phase.name})\n"
        f"WHY THIS STEP: {task.blurb}\n"
        f"METHOD:\n{bullets}\n\n"
        f"COMPANY CONTEXT (live):\n{ctx_md}\n\n"
        f"PRIOR KNOWLEDGE (from their level assessment and completed steps):\n"
        f"{_prior_knowledge(task_id)}\n\n"
        "NEVER START FROM SCRATCH: mine COMPANY CONTEXT and PRIOR KNOWLEDGE "
        "before asking anything. If they already told the system something "
        "(a niche, an audience, an offer idea), take it as INPUT — recap it "
        "in one quick line, then ask only about the genuine gaps this step "
        "still needs. If what's already known substantially covers this "
        "step's deliverable, summarize it back, get one light confirmation, "
        "and complete. Making the mentee repeat themselves is a failure.\n"
    )
    if task.brief:
        base += f"\nFULL STEP BRIEF:\n{task.brief}\n"
    ctx_key = STEP_CONTEXT_KEYS.get(task_id)
    if ctx_key:
        base += (
            f"\nCOMPLETION CONTRACT: when the mentee has explicitly CONFIRMED "
            f"the deliverable, return action='complete' with contextValue = "
            f"the full confirmed content for the '{ctx_key}' company-context "
            f"field (complete and self-contained — it becomes the permanent "
            f"record), and summary = 1-2 sentences of what was decided. "
            f"Never complete without their explicit confirmation."
        )
    else:
        base += (
            "\nCOMPLETION CONTRACT: when the mentee has a concrete plan or "
            "artifact for this step AND confirms they're set, return "
            "action='complete' with summary = 2-3 sentences recording what "
            "they committed to (specific enough that a future session can "
            "pick it up). Never complete without their explicit confirmation."
        )
    return base


def _convo(messages: list[dict]) -> str:
    return "\n".join(
        f"{'COACH' if m['role'] == 'coach' else 'MENTEE'}: {m['text']}"
        for m in messages)


# ---------------------------------------------------------------------------
# Flows
# ---------------------------------------------------------------------------

# Compact copy of the value-creator-level framework summaries (the plugins
# are import-independent; this text is stable framework content shown in the
# roadmap's Your Level panel when both plugins are present).
LEVEL_SUMMARIES = {
    0: ("Curious", "Drawn to AI but not yet holding a concrete app or "
        "service idea — or still missing the basics of what AI does. The "
        "levels page prescribes the road to Level 1."),
    1: ("The Spark", "In love with what AI can do and with one particular "
        "idea. No go-to-market thinking, no wider problem-space view, no "
        "thesis — rolling the dice."),
    2: ("The Listener", "Same passion, plus openness: the idea shifts as "
        "they wrestle with a real problem space and real customers. This is "
        "where profitable side gigs start."),
    3: ("The Amplifier", "Classic entrepreneurship: go-to-market, "
        "distribution, telling the story. Plus the new AI move: using AI "
        "itself to supercharge distribution — AI outbound, voice, AI-driven "
        "content. AI runs across every business function."),
    4: ("The Thesis", "Deep, marinated understanding of the problem space "
        "and a unique, stable thesis for attacking it — one that doesn't "
        "change with each news drop. Venture-scale starts here."),
    5: ("The Oracle", "Understands AI's trend and trajectory in their "
        "specific domain and builds NOW for capabilities that land in 6-12 "
        "months — first through the door, every time."),
}


def levels_installed() -> bool:
    """Is the value-creator-level plugin installed? The two plugins are
    independent — the level gate/section only exist when both are present.
    Checks the user-install dir and the container's bundled dir."""
    candidates = [
        context_store.get_hermes_home() / "plugins" / "value-creator-level" / "plugin.yaml",
    ]
    import pathlib
    candidates.append(pathlib.Path("/opt/hermes/plugins/value-creator-level/plugin.yaml"))
    return any(c.exists() for c in candidates)


def level_status() -> dict:
    """Read the value-creator-level plugin's state (sibling plugin, shared
    volume) — the roadmap is gated on an established badge (only when that
    plugin is installed)."""
    if not levels_installed():
        return {"installed": False, "level": 0, "badge": None,
                "rationale": "", "strengths": [], "checklist": None}
    try:
        path = context_store.get_hermes_home() / "value-creator-level" / "state.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        level = int(data.get("level", 0) or 0)
        badges = data.get("badges") or []
        badge = badges[-1] if badges else None
        history = data.get("history") or []
        last = history[-1] if history else {}
        cl = data.get("checklist") or {}
        items = cl.get("items") or []
        done = sum(1 for i in items if i.get("status") == "done")
        # The mentee's own words from their last level interview + the
        # evidence behind defended prescription steps — real business facts
        # the Coach must never re-ask. Reset on the levels page wipes these
        # (we read the live file every call, so resets propagate instantly).
        answers = [m.get("text", "") for m in (last.get("transcript") or [])
                   if m.get("role") == "builder"]
        interview = " | ".join(a.strip() for a in answers if a.strip())[:1500]
        proven = []
        for i in items:
            if i.get("status") == "done" and i.get("evidence"):
                proven.append(f"{i.get('text', '')[:80]} — evidence: "
                              f"{i['evidence'][:140]}")
        cur = LEVEL_SUMMARIES.get(level)
        nxt = LEVEL_SUMMARIES.get(level + 1)
        return {
            "installed": True,
            "level": level,
            "badge": ({"name": badge.get("name"), "emoji": badge.get("emoji"),
                       "level": badge.get("level")} if badge else None),
            "current": ({"name": cur[0], "summary": cur[1]} if cur else None),
            "next": ({"level": level + 1, "name": nxt[0], "summary": nxt[1]}
                     if nxt else None),
            "rationale": (last.get("rationale") or "")[:400],
            "strengths": [str(x)[:160] for x in (last.get("strengths") or [])][:5],
            "interviewAnswers": interview,
            "provenActions": proven[:6],
            "checklist": ({"done": done, "total": len(items),
                           "targetLevel": cl.get("targetLevel")} if items else None),
        }
    except (OSError, ValueError, TypeError):
        return {"installed": True, "level": 0, "badge": None,
                "rationale": "", "strengths": [], "checklist": None}


def prior_incomplete(task_id: str) -> Optional[str]:
    """For FOUNDATION steps: the title of the previous step if it isn't done
    yet (foundation is strictly sequential); None when clear to start."""
    found = phase_for_task(task_id)
    if not found:
        return None
    phase, task = found
    if not phase.foundation:
        return None
    prog = progress.get_progress()
    for t in phase.tasks:
        if t.id == task_id:
            return None
        if prog.get(t.id, {}).get("status") != "done":
            return t.title
    return None


def start(task_id: str) -> dict:
    if not phase_for_task(task_id):
        return {"error": f"unknown taskId: {task_id}"}
    lv = level_status()
    if lv["installed"] and lv["level"] < 1:
        if lv.get("badge"):
            return {"error": "the roadmap needs an idea — reach Level 1 "
                             "first (your prescription on the Your Level "
                             "page shows the way)"}
        return {"error": "establish your level first — take the assessment "
                         "on the Your Level page"}
    blocker = prior_incomplete(task_id)
    if blocker:
        return {"error": f"finish the previous foundation step first: {blocker}"}
    with _LOCK:
        state = load_state()
        step = _step(state, task_id)
        if step["status"] == "active" and step["messages"]:
            return {"ok": True, "step": step, "already": True}
        opening_schema = {"type": "object",
                          "properties": {"reply": {"type": "string"}},
                          "required": ["reply"]}
        try:
            parsed = _structured(
                _persona(task_id) +
                "\n\nOpen the working session: greet in one line, then ask "
                "the single best first question for this step given the "
                "company context above.",
                "Begin.", opening_schema, temperature=0.6)
            opening = (parsed.get("reply") or "").strip()
        except Exception as exc:
            return {"error": f"coach unavailable: {exc}"}
        if not opening:
            opening = "Let's work this step. Where are you starting from?"
        step["status"] = "active"
        step["startedAt"] = time.time()
        step["messages"] = [{"role": "coach", "text": opening}]
        save_state(state)
        try:
            progress.mark_step_status(task_id, "in-progress")
        except Exception:
            pass
        return {"ok": True, "step": step}


def answer(task_id: str, text: str) -> dict:
    text = (text or "").strip()
    if not text:
        return {"error": "empty answer"}
    with _LOCK:
        state = load_state()
        step = _step(state, task_id)
        if step["status"] != "active":
            return {"error": "no active session for this step"}
        step["messages"].append({"role": "mentee", "text": text})
        n_turns = sum(1 for m in step["messages"] if m["role"] == "mentee")

        instructions = _persona(task_id)
        if n_turns < MIN_TURNS:
            instructions += ("\n\nToo early to complete — reply "
                             "(action='reply') and keep working.")
        elif n_turns >= MAX_TURNS:
            instructions += ("\n\nThis session has run long. Wrap up NOW: "
                             "action='complete' with the best summary" +
                             (" and contextValue" if STEP_CONTEXT_KEYS.get(task_id) else "") +
                             " you can assemble from the work so far.")
        try:
            parsed = _structured(instructions, _convo(step["messages"]),
                                 _TURN_SCHEMA)
        except Exception as exc:
            step["messages"].pop()  # let them resend
            save_state(state)
            return {"error": f"coach unavailable: {exc}"}

        if parsed.get("action") != "complete" and n_turns < MAX_TURNS:
            reply = (parsed.get("reply") or "").strip() or \
                "Say more — specifics."
            step["messages"].append({"role": "coach", "text": reply})
            save_state(state)
            return {"ok": True, "action": "reply", "step": step}

        # complete
        summary = (parsed.get("summary") or "").strip()
        ctx_key = STEP_CONTEXT_KEYS.get(task_id)
        ctx_value = (parsed.get("contextValue") or "").strip()
        closing = "✅ Step complete." + (f" {summary}" if summary else "")
        step["messages"].append({"role": "coach", "text": closing})
        step["status"] = "complete"
        step["completedAt"] = time.time()
        step["summary"] = summary
        save_state(state)
        if ctx_key and ctx_value:
            try:
                context_store.apply_company_context({ctx_key: ctx_value})
            except Exception:
                pass
        try:
            progress.mark_step_status(task_id, "done")
        except Exception:
            pass
        return {"ok": True, "action": "complete", "step": step,
                "summary": summary}


def reset(task_id: str) -> dict:
    """Fresh start for one step: conversation cleared, progress back to todo,
    and (foundation steps) its company-context field cleared — same contract
    as the old kanban reset."""
    if not phase_for_task(task_id):
        return {"error": f"unknown taskId: {task_id}"}
    with _LOCK:
        state = load_state()
        state["steps"][task_id] = {
            "status": "open", "messages": [], "summary": "",
            "startedAt": None, "completedAt": None,
        }
        save_state(state)
    ctx_key = STEP_CONTEXT_KEYS.get(task_id)
    if ctx_key:
        try:
            st = context_store.load_state()
            c = st.get("context")
            if isinstance(c, dict) and ctx_key in c:
                c.pop(ctx_key, None)
                st["context"] = c
                context_store.save_state(st)
                context_store.write_shared_context_file(c)
                context_store.sync_user_profile(c)
        except Exception:
            pass
    try:
        progress.mark_step_status(task_id, "todo")
    except Exception:
        pass
    return {"ok": True}


def public_state() -> dict:
    state = load_state()
    lv = level_status()
    steps = {}
    for phase in ALL_PHASES:
        for task in phase.tasks:
            s = state["steps"].get(task.id) or {}
            steps[task.id] = {
                "status": s.get("status", "open"),
                "messages": s.get("messages", []),
                "summary": s.get("summary", ""),
                "guidance": GUIDANCE.get(task.id, []),
                "lockedBy": prior_incomplete(task.id),
            }
    return {"steps": steps, "levelStatus": lv,
            "levelGate": lv["installed"] and lv["level"] < 1}
