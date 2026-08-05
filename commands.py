"""Slash commands: /value-creator (status) and /value-step <id> (start a step)."""

from __future__ import annotations

from . import progress
from .methodology import ALL_PHASES, phase_for_task

_DOT = {"done": "✓", "in-progress": "◐", "todo": "·"}


def handle_value_creator(raw_args: str) -> str:
    data = progress.roadmap_data()
    pct = round(100 * data["doneTasks"] / data["totalTasks"]) if data["totalTasks"] else 0
    lines = [
        f"**AI Cyber Value Creator™ roadmap** — {pct}% ({data['doneTasks']}/{data['totalTasks']} steps done)",
        "",
    ]
    for phase in data["phases"]:
        tag = " (foundation — do this first)" if phase["foundation"] else ""
        lines.append(f"__{phase['name']}__ — {phase['goal']}{tag}")
        for t in phase["tasks"]:
            mark = _DOT.get(t["status"], "·")
            link = ""
            if t.get("kanban"):
                link = f"  [kanban {t['kanban']['status'] or 'open'}]"
            lines.append(f"  {mark} {t['title']}  (`{t['id']}`){link}")
        lines.append("")
    lines.append("Start a step with `/value-step <step-id>` — it creates a kanban task the")
    lines.append("gateway dispatcher runs as a hermes session.")
    return "\n".join(lines)


def handle_value_step(raw_args: str) -> str:
    step_id = (raw_args or "").strip()
    if not step_id:
        ids = [t.id for p in ALL_PHASES for t in p.tasks]
        return "Usage: /value-step <step-id>\nSteps: " + ", ".join(ids)
    if not phase_for_task(step_id):
        return f"Unknown step id: {step_id}. Run /value-creator to list steps."
    result = progress.open_step_task(step_id)
    if result.get("error"):
        return f"Could not start the step: {result['error']}"
    return (
        f"Started `{step_id}` — kanban task `{result['kanbanTaskId']}` created. "
        "The gateway dispatcher will pick it up and run it as a hermes session "
        "(requires `hermes gateway start`). Track it on the Kanban tab or the "
        "Value Creator roadmap page."
    )
