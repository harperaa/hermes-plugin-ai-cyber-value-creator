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
    STEP_CONTEXT_KEYS,
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


def _find_worker_session(kanban_task_id: str) -> str | None:
    """Locate the worker session for a kanban task by searching session
    messages for the task id (the worker's opening query contains
    "work kanban task <id>"). tasks.session_id only records the ORIGINATING
    session, so claimed tasks need this reverse lookup. Read-only."""
    try:
        import os
        import sqlite3
        try:
            from hermes_constants import get_hermes_home
            db = str(get_hermes_home() / "state.db")
        except ImportError:
            db = os.path.expanduser(
                os.path.join(os.environ.get("HERMES_HOME", "~/.hermes"), "state.db"))
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        try:
            # Exact match on the dispatcher's spawn prompt — a LIKE match
            # bleeds across tasks (any worker that lists the board mentions
            # other task ids in its transcript). Latest attempt wins.
            row = conn.execute(
                "SELECT session_id FROM messages WHERE role = 'user' "
                "AND content = ? ORDER BY id DESC LIMIT 1",
                (f"work kanban task {kanban_task_id}",),
            ).fetchone()
        finally:
            conn.close()
        return row[0] if row else None
    except Exception:
        return None


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
                # the conversation thread (/chat?resume=<session_id>). Always
                # re-resolve for live tasks: the latest respawn wins, and a
                # stale/incorrect cached id self-heals on the next sync.
                sid = None
                if task.status in ("running", "blocked", "done", "in_review", "triage"):
                    sid = _find_worker_session(kid)
                if not sid:
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


def kick_dispatcher(max_spawn: int = 1) -> bool:
    """Run one dispatcher pass NOW so a just-created task spawns immediately
    instead of waiting for the gateway's next 60s tick. Safe anywhere: the
    board lock makes concurrent ticks a no-op, and any failure just leaves
    the task for the normal ticker."""
    try:
        kb = _kanban()
        with kb.connect_closing() as conn:
            kb.dispatch_once(
                conn,
                max_spawn=max_spawn,
                default_assignee=resolve_kanban_assignee(),
            )
        return True
    except Exception:
        return False


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
                priority=10,  # user-initiated: jump the queue
            )
    except Exception as exc:
        return {"error": f"Could not create the kanban task: {exc}"}

    # Fire the dispatcher immediately — the worker session starts within
    # seconds rather than at the next scheduled tick.
    kick_dispatcher()

    links = get_task_links()
    links[task_id] = {"kanbanTaskId": kanban_id, "createdAt": _now_iso()}
    set_task_links(links)
    mark_step_status(task_id, "in-progress")
    return {"ok": True, "kanbanTaskId": kanban_id}


def declare_question(
    kanban_task_id: str,
    number: int | None = None,
    total: int | None = None,
    reason_tag: str | None = None,
) -> dict:
    """Declare the question being asked IN CHAT (the only Q&A surface).

    Posts nothing visible anywhere: it records the interview position (drives
    the roadmap progress bar), and blocks the task on the first question so
    the boards show "answer in chat". Dispatcher-spawned workers must block
    via the NATIVE kanban_block tool (the harness' stop-guard only recognizes
    that tool name in the transcript), so in that context blocking is
    delegated back to the model. Registered as the ``ask_user_question`` tool.
    """
    tag = (reason_tag or "").strip() or (f"Q{int(number)}" if number else "Q")
    if number and total:
        reason = (f"Q{int(number)}/{int(total)} ({tag}): waiting for your answer "
                  "— open the step's chat thread to reply.")
    else:
        reason = f"{tag}: waiting for your answer — open the step's chat thread to reply."
    import os
    in_worker = bool((os.environ.get("HERMES_KANBAN_TASK") or "").strip())
    native_block = False
    try:
        kb = _kanban()
        with kb.connect_closing() as conn:
            task = kb.get_task(conn, kanban_task_id)
            if task is None:
                return {"error": f"unknown kanban task {kanban_task_id}"}
            status = getattr(task, "status", "")
            if status == "triage":
                # Restore the interview's waiting state without a new block event.
                with kb.write_txn(conn):
                    conn.execute(
                        "UPDATE tasks SET status = 'blocked', block_kind = 'needs_input', "
                        "    block_recurrences = 0 WHERE id = ?",
                        (kanban_task_id,),
                    )
            elif status != "blocked":
                if in_worker:
                    native_block = True
                else:
                    kb.block_task(conn, kanban_task_id, reason=reason, kind="needs_input")
    except Exception as exc:
        return {"error": f"could not declare the question: {exc}"}

    # Interview position -> step link (the roadmap progress bar's source).
    if number and total:
        step_id = find_step_for_kanban_task(kanban_task_id)
        if step_id:
            links = get_task_links()
            link = links.get(step_id)
            if link is not None:
                iv = {"n": int(number), "total": int(total)}
                if link.get("interview") != iv:
                    link["interview"] = iv
                    set_task_links(links)
    return {
        "ok": True,
        "taskId": kanban_task_id,
        "status": "awaiting_native_block" if native_block else "blocked",
        "nativeBlock": native_block,
        "blockReason": reason,
    }


def reset_step(task_id: str) -> dict:
    """Reset a step to a clean slate: archive its kanban task (ending the old
    thread), clear the values its interview locked into the company context,
    and drop the link/progress so the step returns to "todo". Deliberately
    does NOT create a new task — the user starts fresh with the + Task button.
    """
    if not phase_for_task(task_id):
        return {"error": f"Unknown taskId: {task_id}"}

    old_kanban_id = (get_task_links().get(task_id) or {}).get("kanbanTaskId")
    if old_kanban_id:
        try:
            kb = _kanban()
            with kb.connect_closing() as conn:
                kb.archive_task(conn, old_kanban_id)
        except Exception:
            pass  # a dead or missing task must not block the reset

    state = load_state()
    (state.get("tasks") or {}).pop(task_id, None)
    (state.get("progress") or {}).pop(task_id, None)
    ctx_key = STEP_CONTEXT_KEYS.get(task_id)
    ctx = state.get("context")
    if ctx_key and isinstance(ctx, dict):
        ctx.pop(ctx_key, None)
    save_state(state)
    if ctx_key:
        # merged_context() backfills empty fields from company-context.md —
        # rewrite the file without this step's value or the old answer
        # resurrects. Merge first so file-only values of OTHER fields survive.
        try:
            from .context_store import merged_context, write_shared_context_file
            cleared = merged_context()
            cleared.pop(ctx_key, None)
            write_shared_context_file(cleared)
        except Exception:
            pass

    return {"ok": True, "archivedTaskId": old_kanban_id, "status": "todo"}


def find_step_for_kanban_task(kanban_task_id: str) -> str | None:
    for tid, link in get_task_links().items():
        if link.get("kanbanTaskId") == kanban_task_id:
            return tid
    return None


# ---------------------------------------------------------------------------
# Roadmap view model (the dashboard/data payload — same shape as the original)
# ---------------------------------------------------------------------------

def roadmap_data() -> dict:
    """Roadmap page payload. Step status is coach-driven (coach.py) — the
    old kanban reconciliation is deliberately NOT run here anymore: stale
    task links from the retired + Task flow must never override the coach's
    statuses. (sync_progress_from_kanban stays for the kanban hooks.)"""
    from .methodology import ALL_PHASES

    progress = get_progress()
    links: dict = {}
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
                    # Q&A happens ONLY in the chat thread — the board just
                    # signals whose turn it is.
                    "awaitingAnswer": bool(
                        link and link.get("kanbanStatus") in ("blocked", "triage")),
                    "kanban": (
                        {
                            "taskId": link.get("kanbanTaskId"),
                            "status": link.get("kanbanStatus"),
                            "sessionId": link.get("sessionId"),
                            "createdAt": link.get("createdAt"),
                            "interview": link.get("interview"),
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
