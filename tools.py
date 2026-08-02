"""Tool handlers.

Contract: ``handler(args: dict, **kwargs) -> str`` (JSON), never raises.
"""

from __future__ import annotations

import json

from . import context_store, progress
from .methodology import (
    ALL_PHASES,
    CONTEXT_FIELD_KEYS,
    CONTEXT_FILE_NAME,
    ELEVATOR_PITCH_KEY,
    phase_for_task,
)

_VALID_FIELDS = [*CONTEXT_FIELD_KEYS, ELEVATOR_PITCH_KEY]


def record_company_context(args: dict, **kwargs) -> str:
    try:
        field = (args.get("field") or "").strip()
        content = args.get("content")
        if field not in _VALID_FIELDS:
            return json.dumps({"error": f"field must be one of: {', '.join(_VALID_FIELDS)}"})
        if not isinstance(content, str) or not content.strip():
            return json.dumps({"error": "content is required"})
        context_store.apply_company_context({field: content})
        return json.dumps(
            {
                "ok": True,
                "field": field,
                "message": (
                    f'Recorded "{field}" in the shared Company Context '
                    f"(live in {CONTEXT_FILE_NAME})."
                ),
            }
        )
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def get_company_context(args: dict, **kwargs) -> str:
    try:
        ctx = context_store.merged_context()
        return json.dumps(
            {
                "context": ctx,
                "contextFile": str(context_store.context_file_path()),
                "offerSummary": context_store.summarize_offer(ctx.get("offer")),
            }
        )
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def value_creator_status(args: dict, **kwargs) -> str:
    try:
        data = progress.roadmap_data()
        foundation = next((p for p in data["phases"] if p["foundation"]), None)
        foundation_done = bool(foundation) and foundation["doneCount"] == foundation["totalCount"]
        next_step = None
        for phase in data["phases"]:
            for task in phase["tasks"]:
                if task["status"] != "done":
                    next_step = {"id": task["id"], "phase": phase["name"], "title": task["title"]}
                    break
            if next_step:
                break
        return json.dumps(
            {
                "phases": data["phases"],
                "totalTasks": data["totalTasks"],
                "doneTasks": data["doneTasks"],
                "foundationComplete": foundation_done,
                "nextStep": next_step,
            }
        )
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def ask_user_question(args: dict, **kwargs) -> str:
    try:
        result = progress.declare_question(
            (args.get("task_id") or "").strip(),
            number=args.get("question_number"),
            total=args.get("question_total"),
            reason_tag=args.get("reason_tag"),
        )
        if result.get("ok"):
            if result.get("nativeBlock"):
                result["message"] = (
                    "Interview position recorded. NOW, in this same turn: "
                    f"(1) call kanban_block(reason={result.get('blockReason', '')!r}, "
                    "kind='needs_input') — REQUIRED: this spawned worker session "
                    "must block through the native tool or the board records a "
                    "protocol violation; (2) END YOUR TURN with the COMPLETE "
                    "question — options as a NUMBERED list — as your final chat "
                    "message, closing with a one-line hint like 'Reply with a "
                    "number or type your answer.' The chat is the ONLY place the user sees the "
                    "question; do NOT post it as a kanban comment. Do NOT call "
                    "clarify in this spawned worker turn — nobody is attached to "
                    "this terminal and it would hang until timeout."
                )
            else:
                result["message"] = (
                    "Interview position recorded; the task shows 'answer in chat'. "
                    "NOW: (a) ONLY if the user's latest message was TYPED here in "
                    "chat (not the 'work kanban task …' spawn prompt), ask the "
                    "question with the clarify tool (options in `choices`, max 4) "
                    "for the quick-select picker; (b) then END YOUR TURN with the "
                    "COMPLETE question — options as a NUMBERED list — as your "
                    "final chat message, closing with a one-line hint like "
                    "'Reply with a number or type your answer.' A bare number in "
                    "chat is a valid answer. The chat is the ONLY place the user "
                    "sees the question; do NOT post it as a kanban comment."
                )
        return json.dumps(result)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def start_value_step(args: dict, **kwargs) -> str:
    try:
        step_id = (args.get("step_id") or "").strip()
        if not phase_for_task(step_id):
            valid = [t.id for p in ALL_PHASES for t in p.tasks]
            return json.dumps({"error": f"Unknown step_id. Valid: {', '.join(valid)}"})
        result = progress.open_step_task(step_id)
        if result.get("error"):
            return json.dumps(result)
        return json.dumps(
            {
                "ok": True,
                "kanbanTaskId": result["kanbanTaskId"],
                "message": (
                    "Step task created on the kanban board — the gateway dispatcher "
                    "will run it as a hermes session (ensure `hermes gateway start` "
                    "is running). Track it on the Kanban tab or the Value Creator "
                    "roadmap."
                ),
            }
        )
    except Exception as exc:
        return json.dumps({"error": str(exc)})
