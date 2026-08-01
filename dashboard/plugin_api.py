"""AI Cyber Value Creator dashboard plugin — backend API routes.

Mounted at /api/plugins/ai-cyber-value-creator/ by the hermes dashboard
plugin system. Thin wrappers around the plugin's core modules (methodology /
context_store / progress); kanban writes go through hermes_cli.kanban_db, the
same code paths the CLI, gateway, and kanban dashboard use.

This file is imported standalone by the dashboard (no package context), so it
loads the plugin package explicitly from the parent directory under a unique
module name.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

try:
    from fastapi import APIRouter, HTTPException
    from fastapi.responses import FileResponse
    from pydantic import BaseModel
except Exception:  # allows unit tests without dashboard dependencies
    class APIRouter:  # type: ignore
        def get(self, *a, **k):
            return lambda fn: fn

        def post(self, *a, **k):
            return lambda fn: fn

    class HTTPException(Exception):  # type: ignore
        def __init__(self, status_code: int, detail: str = ""):
            super().__init__(detail)
            self.status_code = status_code

    class BaseModel:  # type: ignore
        pass

    FileResponse = None  # type: ignore

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_PKG = "hermes_plugin_pkg_ai_cyber_value_creator"


def _core():
    """Load the plugin as a package (once per process) and return its modules."""
    if _PKG not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            _PKG,
            _PLUGIN_ROOT / "__init__.py",
            submodule_search_locations=[str(_PLUGIN_ROOT)],
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load ai-cyber-value-creator core package")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[_PKG] = mod
        try:
            spec.loader.exec_module(mod)
        except Exception:
            sys.modules.pop(_PKG, None)
            raise
    methodology = importlib.import_module(f"{_PKG}.methodology")
    context_store = importlib.import_module(f"{_PKG}.context_store")
    progress = importlib.import_module(f"{_PKG}.progress")
    return methodology, context_store, progress


router = APIRouter()


@router.get("/roadmap")
def get_roadmap():
    methodology, context_store, progress = _core()
    data = progress.roadmap_data()
    ctx = context_store.merged_context()
    pitch_ready = all(
        isinstance(ctx.get(k), str) and ctx[k].strip()
        for k in methodology.CONTEXT_FIELD_KEYS
    )
    data["context"] = {
        "context": ctx,
        "fields": methodology.CONTEXT_FIELDS,
        "offerSummary": context_store.summarize_offer(ctx.get("offer")),
        "pitch": {
            "key": methodology.ELEVATOR_PITCH_KEY,
            "label": methodology.ELEVATOR_PITCH_LABEL,
            "hint": methodology.ELEVATOR_PITCH_HINT,
            "ready": pitch_ready,
        },
        "contextFile": str(context_store.context_file_path()),
    }
    data["centerLabel"] = methodology.CENTER_LABEL
    return data


class StatusBody(BaseModel):
    taskId: str
    status: str


@router.post("/step-status")
def set_step_status(body: StatusBody):
    methodology, _cs, progress = _core()
    if not methodology.phase_for_task(body.taskId):
        raise HTTPException(status_code=404, detail=f"Unknown taskId: {body.taskId}")
    if body.status not in methodology.STATUS_ORDER:
        raise HTTPException(status_code=400, detail=f"status must be one of {methodology.STATUS_ORDER}")
    progress.mark_step_status(body.taskId, body.status)
    return {"ok": True}


class StepBody(BaseModel):
    taskId: str


@router.post("/start-step")
def start_step(body: StepBody):
    _m, _cs, progress = _core()
    result = progress.open_step_task(body.taskId)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/reset-progress")
def reset_progress():
    _m, _cs, progress = _core()
    progress.reset_progress()
    return {"ok": True}


class ContextBody(BaseModel):
    # Free-form patch: {icp, problems, solutions, offer, elevatorPitch}
    model_config = {"extra": "allow"}


@router.post("/context")
def set_context(body: ContextBody):
    _m, context_store, _p = _core()
    patch = {
        k: v
        for k, v in (getattr(body, "model_extra", None) or {}).items()
        if isinstance(v, str)
    }
    context_store.apply_company_context(patch)
    return {"ok": True}


@router.get("/process-diagram")
def process_diagram():
    png = _PLUGIN_ROOT / "assets" / "process-diagram.png"
    if FileResponse is None or not png.exists():
        raise HTTPException(status_code=404, detail="diagram not found")
    return FileResponse(str(png), media_type="image/png")


@router.get("/setup-status")
def setup_status():
    """Onboarding checklist state for the Getting Started card.

    Checks are read-only and never raise: each item resolves to done/pending.
    """
    import json as _json
    import os as _os

    home = Path(_os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))

    grok = bool(_os.environ.get("XAI_API_KEY", "").strip())
    if not grok:
        try:
            store = _json.loads((home / "auth.json").read_text())
            grok = bool(store.get("credential_pool", {}).get("xai-oauth"))
        except Exception:
            grok = False

    def _env_or_dotenv(name: str) -> bool:
        if _os.environ.get(name, "").strip():
            return True
        try:
            for line in (home / ".env").read_text().splitlines():
                if line.strip().startswith(f"{name}=") and line.split("=", 1)[1].strip():
                    return True
        except Exception:
            pass
        return False

    transcript = _env_or_dotenv("TRANSCRIPT_API_KEY")

    model = ""
    try:
        import yaml  # type: ignore
        cfg = yaml.safe_load((home / "config.yaml").read_text()) or {}
        m = cfg.get("model")
        model = (m or {}).get("default", "") if isinstance(m, dict) else str(m or "")
    except Exception:
        pass

    return {
        "grokConnected": grok,
        "transcriptKeySet": transcript,
        "model": model,
        "allDone": grok and transcript,
    }
