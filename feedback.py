"""Weekly mentee feedback — client side.

Assembles the weekly check-in (sentiment + notes + the acknowledged level /
roadmap status snapshot) and submits it server-side to the mentor's
Feedback Hub (separate Railway service). The bearer token never reaches the
browser: the dashboard backend does the POST.

Enabled only when both env vars are set (mirrored into .env by the seed):
  FEEDBACK_HUB_URL    e.g. https://feedback-hub.up.railway.app/ingest
  FEEDBACK_HUB_TOKEN  shared ingest token
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Optional

from . import context_store, progress
from .methodology import ALL_TASK_IDS

WEEK = 7 * 86400


def _env(name: str) -> str:
    v = os.environ.get(name, "").strip()
    if v:
        return v
    try:
        for line in (context_store.get_hermes_home() / ".env").read_text().splitlines():
            line = line.strip()
            if line.startswith(f"{name}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


def configured() -> bool:
    return bool(_env("FEEDBACK_HUB_URL") and _env("FEEDBACK_HUB_TOKEN"))


def _state_path():
    return context_store.get_data_dir() / "feedback.json"


def _load() -> dict:
    try:
        data = json.loads(_state_path().read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    return {"lastSubmittedAt": None, "history": []}


def _save(state: dict) -> None:
    p = _state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp.replace(p)


def freshness(last: Optional[float], now: Optional[float] = None) -> str:
    """green <=7d, yellow <=14d (or never), red >14d."""
    now = now or time.time()
    if last is None:
        return "yellow"
    age = now - last
    if age <= WEEK:
        return "green"
    if age <= 2 * WEEK:
        return "yellow"
    return "red"


def _mentee_email() -> str:
    try:
        from . import mentor_auth
        store = mentor_auth.load_store()
        if store and store.get("email"):
            return str(store["email"])
    except Exception:
        pass
    return os.environ.get("HERMES_DASHBOARD_BASIC_AUTH_USERNAME", "") or "unknown"


def _level_snapshot() -> dict:
    """The value-creator-level status (absent plugin -> empty snapshot)."""
    out: dict[str, Any] = {"level": None, "levelName": "",
                           "checklistDone": None, "checklistTotal": None}
    try:
        path = context_store.get_hermes_home() / "value-creator-level" / "state.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        out["level"] = int(data.get("level", 0) or 0)
        badges = data.get("badges") or []
        if badges:
            out["levelName"] = badges[-1].get("name", "")
        items = (data.get("checklist") or {}).get("items") or []
        if items:
            out["checklistDone"] = sum(1 for i in items if i.get("status") == "done")
            out["checklistTotal"] = len(items)
    except Exception:
        pass
    return out


def _roadmap_snapshot() -> dict:
    try:
        prog = progress.get_progress()
        done = sum(1 for t in ALL_TASK_IDS
                   if prog.get(t, {}).get("status") == "done")
        return {"roadmapDone": done, "roadmapTotal": len(ALL_TASK_IDS)}
    except Exception:
        return {"roadmapDone": None, "roadmapTotal": None}


def status() -> dict:
    state = _load()
    last = state.get("lastSubmittedAt")
    return {
        "configured": configured(),
        "lastSubmittedAt": last,
        "freshness": freshness(last),
    }


def submit(sentiment: str, note: str, activities: str, stuck: str,
           status_ack: bool) -> dict:
    if not configured():
        return {"error": "feedback hub not configured"}
    if sentiment not in ("green", "yellow", "red"):
        return {"error": "pick how your week went (the traffic light)"}
    if not status_ack:
        return {"error": "the status acknowledgement is required"}
    payload = {
        "email": _mentee_email(),
        "name": "",   # future: collected during onboarding
        "sentiment": sentiment,
        "note": (note or "").strip()[:2000],
        "activities": (activities or "").strip()[:8000],
        "stuck": (stuck or "").strip()[:8000],
        "statusAck": True,
    }
    payload.update(_level_snapshot())
    payload.update(_roadmap_snapshot())

    req = urllib.request.Request(
        _env("FEEDBACK_HUB_URL"),
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {_env('FEEDBACK_HUB_TOKEN')}",
                 "Content-Type": "application/json",
                 "User-Agent": "hermes-plugins-feedback/1"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode())
        if not body.get("ok"):
            return {"error": f"hub rejected the submission: {body}"}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:200]
        return {"error": f"hub error {exc.code}: {detail}"}
    except Exception as exc:
        return {"error": f"could not reach the feedback hub: {exc}"}

    state = _load()
    state["lastSubmittedAt"] = time.time()
    state.setdefault("history", []).append(
        {"at": state["lastSubmittedAt"], "sentiment": sentiment,
         "note": payload["note"]})
    state["history"] = state["history"][-52:]
    _save(state)
    return {"ok": True, "status": status()}
