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
import os
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


_BUILD_CACHE: list = []


def _build_version() -> str:
    """The version shown in the page footer, always YYYY.MMDD.HHMM.

    Distribution containers bake HPD_VERSION at docker build — that IS the
    release version. Dev checkouts fall back to the plugin's last commit
    timestamp rendered in the same format, so every install reads alike."""
    if not _BUILD_CACHE:
        version = (os.environ.get("HPD_VERSION") or "").strip()
        if not version:
            try:
                import subprocess
                from pathlib import Path
                # Same pinned zone as build-image.sh version tags, so the dev
                # footer and release tags read on one wall clock.
                env = dict(os.environ, TZ="America/New_York")
                version = subprocess.run(
                    ["git", "-C", str(Path(__file__).resolve().parent.parent),
                     "show", "-s", "--format=%cd",
                     "--date=format-local:%Y.%m%d.%H%M", "HEAD"],
                    capture_output=True, text=True, timeout=3, env=env,
                ).stdout.strip()
            except Exception:
                version = ""
        _BUILD_CACHE.append(version)
    return _BUILD_CACHE[0]


def _ensure_provider_timeouts() -> None:
    """Grok reasoning models sit silent for minutes mid-thought; the default
    stream stale-timeout kills those streams and analysis workers die in
    retry loops. Fresh volumes get 900s from the seed; this backfills
    EXISTING volumes on redeploy. Only sets when absent — a mentee's own
    explicit value is never overwritten."""
    try:
        from hermes_cli.config import load_config, save_config
        cfg = load_config() or {}
        providers = cfg.setdefault("providers", {})
        changed = False
        for pid in ("xai-oauth", "xai"):
            entry = providers.setdefault(pid, {})
            if not isinstance(entry, dict):
                continue
            if "stale_timeout_seconds" not in entry:
                entry["stale_timeout_seconds"] = 900
                changed = True
        if changed:
            save_config(cfg)
    except Exception:
        pass


def _heal_provider_mismatch() -> None:
    """Self-heal the grok family/oauth provider mixup.

    Several upstream paths (model picker families, provider re-inference on
    model change) can write ``model.provider: xai`` — the API-key provider —
    even though the mentee connected via xai-oauth. An explicitly selected
    API-key provider is authoritative in hermes' resolver, so chat init then
    fails with "No usable credentials... Set XAI_API_KEY." while the OAuth
    token sits connected. When we see exactly that state (provider xai, no
    usable XAI_API_KEY, xai-oauth pool entry present) flip config — and any
    cron pins — to xai-oauth. Idempotent, narrow, silent otherwise."""
    try:
        import os as _os
        from hermes_cli.config import load_config, save_config, get_env_value_prefer_dotenv
        cfg = load_config() or {}
        mb = cfg.get("model")
        if not isinstance(mb, dict) or (mb.get("provider") or "").strip() != "xai":
            return
        key = (get_env_value_prefer_dotenv("XAI_API_KEY")
               or _os.environ.get("XAI_API_KEY") or "").strip()
        if key:
            return  # API-key path genuinely configured — not our case
        try:
            from hermes_cli.auth import _load_auth_store
            pool = ((_load_auth_store() or {}).get("credential_pool") or {})
            if not pool.get("xai-oauth"):
                return  # no oauth either — nothing to heal toward
        except Exception:
            return
        mb["provider"] = "xai-oauth"
        cfg["model"] = mb
        save_config(cfg)
        try:
            from cron import jobs as cron_jobs
            for name in ("youtube-intelligence-refresh", "youtube-content-pipeline"):
                job = cron_jobs.resolve_job_ref(name)
                if job and (job.get("provider") or "") == "xai":
                    cron_jobs.update_job(job["id"], {"provider": "xai-oauth"})
        except Exception:
            pass
    except Exception:
        pass


@router.get("/roadmap")
def get_roadmap():
    _heal_provider_mismatch()
    _ensure_provider_timeouts()
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
    # Version footer — always YYYY.MMDD.HHMM (release tag in the container,
    # last plugin commit timestamp in dev).
    data["build"] = _build_version()
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


@router.post("/reset-step")
def reset_step(body: StepBody):
    """Restart one step: archive its kanban task, clear the context values its
    interview locked in, and open a fresh task (questioning restarts at Q1)."""
    _m, _cs, progress = _core()
    result = progress.reset_step(body.taskId)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/reset-progress")
def reset_progress():
    _m, _cs, progress = _core()
    progress.reset_progress()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Roadmap Coach — per-step in-page interviews (host-owned LLM; no kanban)
# ---------------------------------------------------------------------------

def _coach():
    _core()  # ensures the plugin package is registered in this process
    return importlib.import_module(f"{_PKG}.coach")


def _coach_result(result: dict) -> dict:
    if result.get("error"):
        detail = str(result["error"])
        code = 503 if "coach unavailable" in detail else 409
        raise HTTPException(status_code=code, detail=detail)
    return result


@router.get("/coach")
def coach_state() -> dict:
    return _coach().public_state()


class CoachStartBody(BaseModel):
    taskId: str = ""


class CoachAnswerBody(BaseModel):
    taskId: str = ""
    text: str = ""


@router.post("/coach/start")
def coach_start(body: CoachStartBody) -> dict:
    return _coach_result(_coach().start(body.taskId))


@router.post("/coach/answer")
def coach_answer(body: CoachAnswerBody) -> dict:
    return _coach_result(_coach().answer(body.taskId, body.text))


@router.post("/coach/reset")
def coach_reset(body: CoachStartBody) -> dict:
    return _coach_result(_coach().reset(body.taskId))


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

    Checks are read-only and never raise: each item resolves to done/pending
    (plus the one write-path exception: the provider-mismatch self-heal).
    """
    _heal_provider_mismatch()
    _ensure_provider_timeouts()
    import json as _json
    import os as _os

    home = Path(_os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))

    # ANY configured LLM provider counts: a provider API key in env/.env, or
    # any OAuth credential hermes has stored (xai, anthropic, nous, codex, …).
    _PROVIDER_ENV_KEYS = (
        "ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "OPENAI_API_KEY",
        "OPENROUTER_API_KEY", "XAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY",
        "NOUS_API_KEY", "GLM_API_KEY", "KIMI_API_KEY", "MINIMAX_API_KEY",
        "GITHUB_TOKEN",
    )
    llm = False
    try:
        store = _json.loads((home / "auth.json").read_text())
        pools = store.get("credential_pool", {}) or {}
        # Only non-empty credential lists count — the "providers" section is
        # bookkeeping state and can be truthy with zero real credentials.
        llm = any(isinstance(v, list) and len(v) > 0 for v in pools.values())
    except Exception:
        llm = False

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

    if not llm:
        llm = any(_env_or_dotenv(k) for k in _PROVIDER_ENV_KEYS)

    transcript = _env_or_dotenv("TRANSCRIPT_API_KEY")

    # Image generation readiness: xAI (any credential) is the preferred
    # provider; GEMINI_API_KEY is the sanctioned fallback when xAI isn't used.
    xai = _env_or_dotenv("XAI_API_KEY")
    if not xai:
        try:
            store = _json.loads((home / "auth.json").read_text())
            pools = store.get("credential_pool", {}) or {}
            xai = any(k.startswith("xai") and isinstance(v, list) and len(v) > 0
                      for k, v in pools.items())
        except Exception:
            xai = False
    gemini = _env_or_dotenv("GEMINI_API_KEY")
    image_gen = bool(xai or gemini)

    model = ""
    try:
        import yaml  # type: ignore
        cfg = yaml.safe_load((home / "config.yaml").read_text()) or {}
        m = cfg.get("model")
        model = (m or {}).get("default", "") if isinstance(m, dict) else str(m or "")
    except Exception:
        pass

    return {
        "llmConnected": llm,
        "grokConnected": llm,  # legacy alias for older dashboard bundles
        "transcriptKeySet": transcript,
        "xaiConnected": bool(xai),
        "geminiKeySet": bool(gemini),
        "imageGenReady": image_gen,
        "model": model,
        "allDone": llm and transcript and image_gen,
    }


# ---------------------------------------------------------------------------
# Update check — is a newer image published than the one running?
# The published version is mirrored to an unlisted gist at publish time
# (containers can't auth to the private GHCR/GitHub). Cached 1h in-process.
# ---------------------------------------------------------------------------
_BEACON_GIST = os.environ.get("HPD_BEACON_GIST", "53cc65f66a044777e930e044d43e49eb")
_UPDATE_CACHE: dict = {"at": 0.0, "latest": ""}


def _latest_published_version() -> str:
    import json as _json
    import time as _time
    import urllib.request
    now = _time.time()
    if _UPDATE_CACHE["latest"] and now - _UPDATE_CACHE["at"] < 3600:
        return _UPDATE_CACHE["latest"]
    latest = ""
    for url, extract in (
        (f"https://api.github.com/gists/{_BEACON_GIST}",
         lambda b: _json.loads(b)["files"]["VERSION"]["content"]),
        (f"https://gist.githubusercontent.com/harperaa/{_BEACON_GIST}/raw/VERSION",
         lambda b: b.decode()),
    ):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "curl/8.4.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                latest = extract(resp.read()).strip()
            if latest:
                break
        except Exception:
            continue
    if latest:
        _UPDATE_CACHE["latest"] = latest
        _UPDATE_CACHE["at"] = now
    return latest


@router.get("/update-check")
def update_check() -> dict:
    current = (os.environ.get("HPD_VERSION") or "").strip()
    latest = _latest_published_version()
    project = os.environ.get("RAILWAY_PROJECT_ID", "")
    service = os.environ.get("RAILWAY_SERVICE_ID", "")
    environment = os.environ.get("RAILWAY_ENVIRONMENT_ID", "")
    railway_url = ""
    if project and service:
        railway_url = (f"https://railway.com/project/{project}"
                       f"/service/{service}"
                       + (f"?environmentId={environment}" if environment else ""))
    return {
        # No HPD_VERSION (dev checkout) -> never claim an update.
        "updateAvailable": bool(current and latest and latest != current),
        "current": current,
        "latest": latest,
        "railwayUrl": railway_url,
    }


# ---------------------------------------------------------------------------
# Weekly mentee feedback (mentor's Feedback Hub — separate service)
# ---------------------------------------------------------------------------

def _feedback():
    import importlib
    _core()
    return importlib.import_module(f"{_PKG}.feedback")


@router.get("/feedback/status")
def feedback_status() -> dict:
    return _feedback().status()


class FeedbackBody(BaseModel):
    sentiment: str = ""
    note: str = ""
    activities: str = ""
    stuck: str = ""
    statusAck: bool = False
    name: str = ""
    email: str = ""
    nextStep: str = ""


@router.post("/feedback/submit")
def feedback_submit(body: FeedbackBody) -> dict:
    result = _feedback().submit(body.sentiment, body.note, body.activities,
                                body.stuck, body.statusAck,
                                name=body.name, email=body.email,
                                next_step=body.nextStep)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=str(result["error"]))
    return result


@router.post("/pin-cron")
def pin_cron():
    """Pin the two scheduled jobs to the mentee's connected provider.

    Blank-model deployments create the jobs unpinned; once a provider is
    connected, the spend-drift guard would skip them on the next config
    change. Called by the Getting Started card the first time it sees an
    LLM connected. Idempotent.
    """
    try:
        from hermes_cli.config import load_config
        from hermes_cli.models import get_default_model_for_provider
        from cron import jobs as cron_jobs
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"hermes modules unavailable: {exc}")

    cfg = load_config() or {}
    mb = cfg.get("model")
    provider = (mb or {}).get("provider", "") if isinstance(mb, dict) else ""
    model = (mb or {}).get("default", "") if isinstance(mb, dict) else str(mb or "")
    if not provider:
        raise HTTPException(status_code=409, detail="no provider configured yet")
    if not model:
        base = provider.replace("-oauth", "")
        model = (get_default_model_for_provider(provider)
                 or get_default_model_for_provider(base) or "")
    if not model:
        raise HTTPException(status_code=409, detail=f"no default model known for provider {provider!r}")

    pinned = []
    for name in ("youtube-intelligence-refresh", "youtube-content-pipeline"):
        try:
            job = cron_jobs.resolve_job_ref(name)
            if not job:
                continue
            if job.get("provider") and job.get("model"):
                pinned.append({"name": name, "already": True})
                continue
            cron_jobs.update_job(job["id"], {"provider": provider, "model": model})
            pinned.append({"name": name, "provider": provider, "model": model})
        except Exception as exc:
            pinned.append({"name": name, "error": str(exc)})
    return {"ok": True, "provider": provider, "model": model, "jobs": pinned}


