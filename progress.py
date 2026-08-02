"""Roadmap progress + hermes-kanban task linkage.

Each roadmap step can be "started" — that creates a kanban task (title
``"<Phase>: <Step title>"``, body = the executive brief) which the gateway's
dispatcher picks up and runs as a normal hermes session. The kanban task id is
stored as the step's link; step status is derived from the kanban task's
state (same reconciliation rules as the paperclip original's issues):

* kanban ``done``                     → step ``done``
* any live (non-archived) open state  → step ``in-progress`` (if still todo)
* link missing but a task with the deterministic title exists → re-adopt it.

All kanban access goes through ``hermes_cli.kanban_db`` — the same code paths
the CLI, gateway, and kanban dashboard use — imported lazily so this module
still imports in environments without hermes on the path.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .context_store import get_data_dir, load_state, save_state
from .methodology import (
    ALL_TASK_IDS,
    PLAYBOOK_SKILL_SLUG,
    STEP_SKILLS,
    build_task_description,
    phase_for_task,
    step_task_title,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _kanban():
    """Import hermes' kanban kernel lazily (present in any hermes process)."""
    from hermes_cli import kanban_db
    return kanban_db


# ---------------------------------------------------------------------------
# Progress store
# ---------------------------------------------------------------------------

def get_progress() -> dict[str, dict]:
    p = load_state().get("progress")
    return dict(p) if isinstance(p, dict) else {}


def set_progress(progress: dict[str, dict]) -> None:
    state = load_state()
    state["progress"] = progress
    save_state(state)


def mark_step_status(task_id: str, status: str) -> None:
    progress = get_progress()
    if progress.get(task_id, {}).get("status") == status:
        return
    progress[task_id] = {"status": status, "updatedAt": _now_iso()}
    set_progress(progress)


def reset_progress() -> None:
    state = load_state()
    state["progress"] = {}
    state["tasks"] = {}
    save_state(state)


def get_task_links() -> dict[str, dict]:
    links = load_state().get("tasks")
    return dict(links) if isinstance(links, dict) else {}


def set_task_links(links: dict[str, dict]) -> None:
    state = load_state()
    state["tasks"] = links
    save_state(state)


# ---------------------------------------------------------------------------
# Kanban linkage
# ---------------------------------------------------------------------------

def reconcile_task_links(links: dict[str, dict]) -> dict[str, dict]:
    """Re-adopt step→kanban links for steps whose link is missing by matching
    the deterministic task title against live kanban tasks (most recent wins)."""
    missing = [tid for tid in ALL_TASK_IDS if not links.get(tid, {}).get("kanbanTaskId")]
    if not missing:
        return links
    try:
        kb = _kanban()
        with kb.connect_closing() as conn:
            tasks = kb.list_tasks(conn, include_archived=False)
    except Exception:
        return links

    by_title: dict[str, Any] = {}
    for t in tasks:
        title = getattr(t, "title", None)
        if not title:
            continue
        prev = by_title.get(title)
        if prev is None or (getattr(t, "created_at", 0) or 0) > (getattr(prev, "created_at", 0) or 0):
            by_title[title] = t

    changed = False
    for tid in missing:
        found = phase_for_task(tid)
        if not found:
            continue
        match = by_title.get(step_task_title(*found))
        if match is None:
            continue
        links[tid] = {"kanbanTaskId": match.id, "createdAt": _now_iso()}
        changed = True
    if changed:
        set_task_links(links)
    return links


def _step_status_from_kanban(kanban_status: str | None, current: str) -> str:
    if kanban_status == "done":
        return "done"
    if kanban_status and kanban_status != "archived" and current == "todo":
        return "in-progress"
    return current


def sync_progress_from_kanban() -> tuple[dict[str, dict], dict[str, dict]]:
    """Reconcile links + derive each linked step's status from its kanban task.
    Returns (progress, links) after any updates were persisted."""
    progress = get_progress()
    links = reconcile_task_links(get_task_links())
    if not links:
        return progress, links
    try:
        kb = _kanban()
        with kb.connect_closing() as conn:
            changed = False
            for tid, link in links.items():
                kid = link.get("kanbanTaskId")
                if not kid:
                    continue
                task = kb.get_task(conn, kid)
                if task is None:
                    continue
                # Surface the worker session id so the dashboard can deep-link
                # the conversation thread (/chat?resume=<session_id>).
                sid = getattr(task, "session_id", None)
                if sid and link.get("sessionId") != sid:
                    link["sessionId"] = sid
                    changed = True
                if link.get("kanbanStatus") != task.status:
                    link["kanbanStatus"] = task.status
                    changed = True
                cur = progress.get(tid, {}).get("status", "todo")
                nxt = _step_status_from_kanban(task.status, cur)
                if nxt != cur:
                    progress[tid] = {"status": nxt, "updatedAt": _now_iso()}
                    changed = True
            if changed:
                state = load_state()
                state["progress"] = progress
                state["tasks"] = links
                save_state(state)
    except Exception:
        pass  # best-effort — the dashboard still renders from stored state
    return progress, links


def resolve_kanban_assignee() -> str:
    """kanban.default_assignee from hermes config, else the base profile.

    Tasks created unassigned sit on the board flagged NEEDS ASSIGNEE and the
    dispatcher never claims them — every task we create must be born assigned.
    """
    try:
        from hermes_cli.config import load_config
        val = ((load_config() or {}).get("kanban", {}) or {}).get("default_assignee")
        if isinstance(val, str) and val.strip():
            return val.strip()
    except Exception:
        pass
    return "default"


def open_step_task(task_id: str) -> dict:
    """Create a fresh kanban task for a roadmap step, link it, and put the
    step in progress. The gateway dispatcher spawns the worker session."""
    found = phase_for_task(task_id)
    if not found:
        return {"error": f"Unknown taskId: {task_id}"}
    phase, task = found
    skills = ["ai-cyber-value-creator:" + PLAYBOOK_SKILL_SLUG, "ai-cyber-value-creator:company-context"]
    step_skill = STEP_SKILLS.get(task_id)
    if step_skill:
        skills.append("ai-cyber-value-creator:" + step_skill)
    try:
        kb = _kanban()
        with kb.connect_closing() as conn:
            kanban_id = kb.create_task(
                conn,
                title=step_task_title(phase, task),
                body=build_task_description(phase, task, context_dir=str(get_data_dir())),
                assignee=resolve_kanban_assignee(),
                created_by="ai-cyber-value-creator",
                workspace_kind="scratch",
                skills=skills,
            )
    except Exception as exc:
        return {"error": f"Could not create the kanban task: {exc}"}

    links = get_task_links()
    links[task_id] = {"kanbanTaskId": kanban_id, "createdAt": _now_iso()}
    set_task_links(links)
    mark_step_status(task_id, "in-progress")
    return {"ok": True, "kanbanTaskId": kanban_id}


def find_step_for_kanban_task(kanban_task_id: str) -> str | None:
    for tid, link in get_task_links().items():
        if link.get("kanbanTaskId") == kanban_task_id:
            return tid
    return None


# ---------------------------------------------------------------------------
# Roadmap view model (the dashboard/data payload — same shape as the original)
# ---------------------------------------------------------------------------

def roadmap_data() -> dict:
    from .methodology import ALL_PHASES

    progress, links = sync_progress_from_kanban()
    phases = []
    done_total = 0
    for phase in ALL_PHASES:
        tasks = []
        for task in phase.tasks:
            p = progress.get(task.id, {})
            link = links.get(task.id) or None
            tasks.append(
                {
                    "id": task.id,
                    "title": task.title,
                    "blurb": task.blurb,
                    "status": p.get("status", "todo"),
                    "updatedAt": p.get("updatedAt"),
                    "kanban": (
                        {
                            "taskId": link.get("kanbanTaskId"),
                            "status": link.get("kanbanStatus"),
                            "sessionId": link.get("sessionId"),
                            "createdAt": link.get("createdAt"),
                        }
                        if link and link.get("kanbanTaskId")
                        else None
                    ),
                }
            )
        done_count = sum(1 for t in tasks if t["status"] == "done")
        done_total += done_count
        phases.append(
            {
                "id": phase.id,
                "name": phase.name,
                "color": phase.color,
                "goal": phase.goal,
                "gateToNext": phase.gate_to_next,
                "foundation": phase.foundation,
                "tasks": tasks,
                "doneCount": done_count,
                "totalCount": len(tasks),
            }
        )
    return {
        "phases": phases,
        "totalTasks": len(ALL_TASK_IDS),
        "doneTasks": done_total,
    }
