"""Personal Automation gallery — our blueprints as editable forms.

Upstream Hermes ships a hardcoded blueprint gallery on the Cron page. This
module exposes the *installed* skill blueprints (the hermes-personal-automation
collection, in curriculum order, then any other installed blueprint skill) as
form schemas the dashboard bundle renders alongside it, and turns a filled
form into the same ``blueprint:<name>`` job the ``/suggestions accept`` path
creates — with the mentee's edits applied (schedule, delivery, focus prompt,
per-skill config such as city or file paths).

Nothing here bypasses consent: a job exists only after the mentee clicks
Schedule. Pending suggestions stay listed; scheduling from here marks the
matching suggestion accepted so the two surfaces agree.
"""
from __future__ import annotations

import dataclasses
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# The order the workshop teaches them — level 0 first. Anything else installed
# with a blueprint block follows, alphabetically.
CURRICULUM = [
    "secure-box-audit", "return-desk", "out-the-door-brief", "money-watch",
    "expiry-desk", "quiet-inbox", "sunday-kitchen", "people-file",
    "morning-standup", "boot-health-check", "sunday-ledger",
]

JOB_PREFIX = "blueprint:"
_DOW = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

# The input files each blueprint reads, with the example content the workshop
# ships. ``kind`` is "file" (one editable file) or "dir" (a folder of files;
# ``files`` are the starter files). Anything else is a plain value.
_T_RENEWALS = (
    "name,date,lead_days,note\n"
    "Passport,2027-03-23,270,\"6 months validity needed for Asia\"\n"
    "Car insurance,2026-10-08,21,\"quotes are cheapest ~3 weeks out\"\n"
    "Domain example.com,2026-12-01,30,\"auto-renews at full price\"\n"
)
_T_WATCHLIST = (
    "type | label | url | threshold | notes\n"
    "price | Standing desk | https://example.com/desk | 320 | alert when at or below 320\n"
    "stock | Concert tickets | https://example.com/tickets | in stock | any availability\n"
    "protect | Headphones price protection | https://example.com/order/123 | 2026-10-01 | claim window closes\n"
)
_T_PURCHASES = (
    "| Item | Bought | Return window | Warranty | Notes |\n"
    "|---|---|---|---|---|\n"
    "| Wireless headphones | 2026-09-01 | 30 days | 2 years | Best Buy |\n"
    "| Streaming trial | 2026-09-10 | 14 days | - | cancel before it converts |\n"
)
_T_INVENTORY = (
    "chicken thighs — 1 lb — 2026-09-08\n"
    "spinach — 1 bag — 2026-09-04\n"
    "eggs — 6 — 2026-09-23\n"
    "rice — 2 lb — 2027-01-01\n"
)
_T_PREFERENCES = "No shellfish. Have an oven and a wok. Two vegetarian dinners a week. Weeknight dinners under 40 minutes.\n"
_T_COMMITMENTS = "- [ ] send proposal | Sam | 2026-09-08 | email\n- [ ] return the drill | Priya | 2026-09-12 | in person\n"
_T_CALENDAR = "09:00 team standup; 14:00 dentist\n"
_T_PERSON = (
    "---\n"
    "name: Sam Okafor\n"
    "birthday: 1988-09-13\n"
    "last_contact: 2026-03-01\n"
    "---\n"
    "- 2026-03-01 — Called. New job at a logistics startup. Nervous about managing people.\n"
    "- 2026-01-14 — Mentioned wanting a proper chef's knife. Owns none.\n"
)
_T_PERSON_2 = (
    "---\n"
    "name: Priya Natarajan\n"
    "birthday: 1991-11-02\n"
    "last_contact: 2026-08-20\n"
    "---\n"
    "- 2026-08-20 — Coffee. Training for a half marathon in October; asked about my Sunday ledger habit.\n"
    "- 2026-05-03 — Her mom had surgery; recovering well. Follow up before Thanksgiving.\n"
)
_T_PERSON_3 = (
    "---\n"
    "name: Marcus Bell\n"
    "birthday: 1979-01-27\n"
    "last_contact: 2025-12-15\n"
    "---\n"
    "- 2025-12-15 — Holiday call. Talked about selling the boat and finally taking the Portugal trip.\n"
    "- 2025-09-08 — Sent him the vCISO offer outline; he offered an intro to two MSP owners.\n"
)
_T_PERSON_4 = (
    "---\n"
    "name: Dana Whitfield\n"
    "birthday: 1985-06-18\n"
    "last_contact: 2026-09-01\n"
    "---\n"
    "- 2026-09-01 — Text. Kids back in school; she is picking up piano again.\n"
    "- 2026-06-18 — Birthday dinner. Loved the ramen place; wants to try the omakase next time.\n"
)
_PEOPLE_STARTERS = [
    {"name": "people/sam-okafor.md", "template": _T_PERSON},
    {"name": "people/priya-natarajan.md", "template": _T_PERSON_2},
    {"name": "people/marcus-bell.md", "template": _T_PERSON_3},
    {"name": "people/dana-whitfield.md", "template": _T_PERSON_4},
]

INPUT_FILES: Dict[str, Dict[str, Any]] = {
    "expiry_desk.renewals_path": {"kind": "file", "files": [{"name": "", "template": _T_RENEWALS}],
                                  "hint": "CSV: name, date (YYYY-MM-DD), lead_days, note"},
    "money_watch.watchlist_path": {"kind": "file", "files": [{"name": "", "template": _T_WATCHLIST}],
                                   "hint": "one row per thing to watch: type (price | stock | protect), label, url, threshold, notes"},
    "return_desk.ledger_path": {"kind": "file", "files": [{"name": "", "template": _T_PURCHASES}],
                                "hint": "markdown table: Item, Bought (YYYY-MM-DD), Return window, Warranty, Notes"},
    "sunday_kitchen.inventory_path": {"kind": "file", "files": [{"name": "", "template": _T_INVENTORY}],
                                      "hint": "one line per item: name — quantity — use-by date"},
    "sunday_kitchen.preferences_path": {"kind": "file", "files": [{"name": "", "template": _T_PREFERENCES}],
                                        "hint": "plain sentences: allergies, equipment, how many vegetarian nights, time limits"},
    "quiet_inbox.commitments_path": {"kind": "file", "files": [{"name": "", "template": _T_COMMITMENTS}],
                                     "hint": "one line per promise: - [ ] what | to whom | by when | channel"},
    "morning_standup.ledger_path": {"kind": "dir", "files": [{"name": "commitments.md", "template": _T_COMMITMENTS},
                                                            {"name": "today-calendar.md", "template": _T_CALENDAR}],
                                    "hint": "a folder other jobs drop files into; today-calendar.md and commitments.md are the ones it reads first"},
    "quiet_inbox.drafts_path": {"kind": "dir", "files": [],
                                "hint": "the job writes draft replies here as separate files; nothing to prepare"},
    "people_file.vault_path": {"kind": "dir", "files": list(_PEOPLE_STARTERS),
                               "hint": "one markdown file per person under people/, with name, birthday and last_contact in the front matter — four sample people are offered as starters"},
    "sunday_ledger.vault_path": {"kind": "dir", "files": [{"name": "renewals.csv", "template": _T_RENEWALS},
                                                         {"name": "purchases.md", "template": _T_PURCHASES},
                                                         {"name": "ledger/commitments.md", "template": _T_COMMITMENTS}] + list(_PEOPLE_STARTERS),
                                 "hint": "the whole life folder: renewals.csv, purchases.md, ledger/commitments.md, people/"},
}


# ---------------------------------------------------------------------------
# Hermes' own blueprint helpers, loaded by path: this plugin ships a
# ``tools.py`` of its own, so ``import tools.blueprints`` is ambiguous when the
# plugin directory is first on sys.path (pytest, ad-hoc scripts).
# ---------------------------------------------------------------------------

_BP_MOD = None


def _bp():
    global _BP_MOD
    if _BP_MOD is None:
        import importlib.util
        import cron  # unambiguous — locates the Hermes checkout
        path = Path(cron.__file__).resolve().parent.parent / "tools" / "blueprints.py"
        import sys
        spec = importlib.util.spec_from_file_location("_hermes_tools_blueprints", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod      # dataclasses resolve hints via sys.modules
        spec.loader.exec_module(mod)
        _BP_MOD = mod
    return _BP_MOD


# ---------------------------------------------------------------------------
# discovery
# ---------------------------------------------------------------------------

def _skill_files() -> List[Path]:
    """Every SKILL.md under every skills directory Hermes knows about."""
    out: List[Path] = []
    try:
        from agent.skill_utils import get_all_skills_dirs, iter_skill_index_files
        for d in get_all_skills_dirs():
            if d.is_dir():
                out.extend(iter_skill_index_files(d, "SKILL.md"))
    except Exception:
        logger.debug("skill discovery via skill_utils failed", exc_info=True)
    if not out:
        try:
            from . import context_store
            root = context_store.get_hermes_home() / "skills"
            out = list(root.glob("*/SKILL.md")) + list(root.glob("*/*/SKILL.md"))
        except Exception:
            pass
    return out


def _title_from_body(body: str, fallback: str) -> str:
    for line in (body or "").splitlines():
        m = re.match(r"^#\s+(.+?)\s*$", line.strip())
        if m:
            # "# Secure Box Audit (Level 0)" -> "Secure Box Audit"
            return re.sub(r"\s*\(Level\s*\d+\)\s*$", "", m.group(1)).strip()
    return fallback.replace("-", " ").title()


def _level_from_tags(tags: List[str]) -> Optional[int]:
    for t in tags or []:
        m = re.match(r"^level-(\d+)$", str(t))
        if m:
            return int(m.group(1))
    return None


def _config_current(key: str) -> Optional[str]:
    try:
        from agent.skill_utils import SKILL_CONFIG_PREFIX, _resolve_dotpath
        from hermes_cli.config import load_config_readonly
        v = _resolve_dotpath(load_config_readonly(), f"{SKILL_CONFIG_PREFIX}.{key}")
        return None if v is None else str(v)
    except Exception:
        return None


def _parse_skill(path: Path) -> Optional[Dict[str, Any]]:
    """A gallery entry (without job/suggestion status) for one SKILL.md, or
    None when the skill carries no blueprint block."""
    try:
        from agent.skill_utils import parse_frontmatter
        text = path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        spec = _bp().parse_blueprint(text)
    except Exception:
        logger.debug("cannot parse %s", path, exc_info=True)
        return None
    if spec is None:
        return None
    hermes = ((fm.get("metadata") or {}).get("hermes") or {}) if isinstance(fm, dict) else {}
    tags = [str(t) for t in (hermes.get("tags") or [])]
    fields = []
    for c in hermes.get("config") or []:
        if not isinstance(c, dict) or not c.get("key"):
            continue
        key = str(c["key"])
        default = "" if c.get("default") is None else str(c.get("default"))
        current = _config_current(key)
        meta = INPUT_FILES.get(key)
        fields.append({
            "key": key,
            "label": str(c.get("prompt") or c.get("description") or key),
            "description": str(c.get("description") or ""),
            "default": default,
            "value": current if current is not None else default,
            "kind": (meta or {}).get("kind", "value"),
            "hint": (meta or {}).get("hint", ""),
            "files": list((meta or {}).get("files", [])),
        })
    name = str(fm.get("name") or spec.skill_name or path.parent.name)
    return {
        "name": name,
        "title": _title_from_body(body, name),
        "description": str(fm.get("description") or ""),
        "level": _level_from_tags(tags),
        "tags": [t for t in tags if t not in ("blueprint",) and not t.startswith("level-")],
        "schedule": spec.schedule,
        "scheduleHuman": describe_schedule(spec.schedule),
        "deliver": spec.deliver or "origin",
        "prompt": spec.prompt or "",
        "noAgent": bool(spec.no_agent),
        "model": spec.model,
        "toolsets": list(spec.enabled_toolsets or []),
        "config": fields,
        "path": str(path),
    }


def _deliver_options() -> List[str]:
    opts = ["origin", "local"]
    try:
        from cron.scheduler import cron_delivery_targets
        for t in cron_delivery_targets():
            if t.get("id") and t["id"] not in opts:
                opts.append(str(t["id"]))
    except Exception:
        pass
    return opts


def _job_for(name: str) -> Optional[Dict[str, Any]]:
    try:
        from cron import jobs as cron_jobs
        return cron_jobs.resolve_job_ref(f"{JOB_PREFIX}{name}")
    except Exception:
        return None


def _suggestion_for(name: str) -> Optional[Dict[str, Any]]:
    try:
        from cron.suggestions import load_suggestions
    except Exception:
        return None
    hits = [s for s in load_suggestions()
            if str(s.get("dedup_key") or "").startswith(f"{JOB_PREFIX}{name}:")]
    if not hits:
        return None
    # a pending record wins over stale accepted/dismissed ones
    for st in ("pending", "accepted", "dismissed"):
        for s in hits:
            if s.get("status") == st:
                return s
    return hits[0]


def _schedule_text(job: Dict[str, Any]) -> str:
    sch = job.get("schedule")
    if isinstance(sch, dict):
        return str(sch.get("expr") or sch.get("cron") or sch.get("value") or sch.get("kind") or "")
    return str(sch or "")


def _entry_status(entry: Dict[str, Any]) -> Dict[str, Any]:
    job = _job_for(entry["name"])
    sug = _suggestion_for(entry["name"])
    out = dict(entry)
    if job:
        out["status"] = "scheduled"
        out["job"] = {
            "id": job.get("id"),
            "schedule": _schedule_text(job),
            "scheduleHuman": describe_schedule(_schedule_text(job)),
            "deliver": job.get("deliver") or "origin",
            "prompt": job.get("prompt") or "",
            "model": job.get("model"),
            "enabled": job.get("enabled", True),
            "lastStatus": job.get("last_status"),
            "lastRunAt": job.get("last_run_at"),
            "nextRunAt": job.get("next_run_at"),
        }
    else:
        out["job"] = None
        out["status"] = {"pending": "suggested", "dismissed": "dismissed"}.get(
            (sug or {}).get("status"), "available")
    out["suggestionId"] = (sug or {}).get("id")
    return out


def list_blueprints() -> Dict[str, Any]:
    by_name: Dict[str, Dict[str, Any]] = {}
    for p in _skill_files():
        e = _parse_skill(p)
        if e and e["name"] not in by_name:
            by_name[e["name"]] = e
    ordered = [by_name.pop(n) for n in CURRICULUM if n in by_name]
    ordered += [by_name[n] for n in sorted(by_name)]
    entries = []
    for i, e in enumerate(ordered, 1):
        e = _entry_status(e)
        e["number"] = i
        e["curriculum"] = e["name"] in CURRICULUM
        entries.append(e)
    tz = _server_tz()
    return {"entries": entries, "count": len(entries),
            "deliverOptions": _deliver_options(), "serverTz": tz}


def _server_tz() -> str:
    import os
    import time
    return os.environ.get("TZ") or (time.tzname[0] if time.tzname else "UTC")


# ---------------------------------------------------------------------------
# schedules — human text for a cron expression
# ---------------------------------------------------------------------------

def _hhmm(m: str, h: str) -> Optional[str]:
    if not (m.isdigit() and h.isdigit()):
        return None
    hh, mm = int(h), int(m)
    if not (0 <= hh < 24 and 0 <= mm < 60):
        return None
    suffix = "am" if hh < 12 else "pm"
    h12 = hh % 12 or 12
    return f"{h12}:{mm:02d} {suffix}"


def describe_schedule(expr: str) -> str:
    """Plain English for the cron shapes the forms produce; the raw
    expression for anything else."""
    parts = str(expr or "").split()
    if len(parts) != 5:
        return str(expr or "")
    m, h, dom, mon, dow = parts
    t = _hhmm(m, h)
    if t and dom == "*" and mon == "*":
        if dow == "*":
            return f"every day at {t}"
        if dow in ("1-5", "1,2,3,4,5"):
            return f"weekdays at {t}"
        if dow in ("0,6", "6,0"):
            return f"weekends at {t}"
        if dow.isdigit() and 0 <= int(dow) <= 6:
            return f"every {_DOW[int(dow)]} at {t}"
        if re.fullmatch(r"[0-6](,[0-6])+", dow):
            names = [_DOW[int(d)][:3] for d in dow.split(",")]
            return f"{', '.join(names)} at {t}"
    if t and dom.isdigit() and mon == "*" and dow == "*":
        d = int(dom)
        sfx = "th" if 11 <= d <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(d % 10, "th")
        return f"monthly on the {d}{sfx} at {t}"
    mh = re.fullmatch(r"\*/(\d+)", h)
    if mh and m.isdigit() and dom == "*" and mon == "*" and dow == "*":
        n = int(mh.group(1))
        return "every hour" if n == 1 else f"every {n} hours"
    mm_ = re.fullmatch(r"\*/(\d+)", m)
    if mm_ and h == "*" and dom == "*" and mon == "*" and dow == "*":
        return f"every {mm_.group(1)} minutes"
    return str(expr)


# ---------------------------------------------------------------------------
# actions
# ---------------------------------------------------------------------------

def _find_entry(name: str) -> Optional[Dict[str, Any]]:
    for e in list_blueprints()["entries"]:
        if e["name"] == name:
            return e
    return None


def _validate_schedule(expr: str) -> str:
    expr = str(expr or "").strip()
    if not expr:
        raise ValueError("a schedule is required")
    from cron.jobs import parse_schedule
    parse_schedule(expr)  # raises ValueError with a readable message
    return expr


def _write_config(fields: List[Dict[str, Any]], values: Dict[str, Any]) -> List[str]:
    """Persist edited per-skill config keys via the same path as
    `hermes config set skills.config.<key>`; returns the keys written."""
    written = []
    allowed = {f["key"] for f in fields}
    for key, val in (values or {}).items():
        if key not in allowed:
            continue
        sval = "" if val is None else str(val).strip()
        current = _config_current(key)
        if sval == (current if current is not None else ""):
            continue
        from hermes_cli.config import set_config_value
        set_config_value(f"skills.config.{key}", sval, force=True)
        written.append(key)
    return written


def schedule_blueprint(name: str, *, schedule: Optional[str] = None,
                       deliver: Optional[str] = None, prompt: Optional[str] = None,
                       config: Optional[Dict[str, Any]] = None,
                       model: Optional[str] = None,
                       origin: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create (or update) the ``blueprint:<name>`` job with the form's edits."""
    entry = _find_entry(name)
    if entry is None:
        return {"error": f"no installed blueprint named '{name}'"}
    expr = _validate_schedule(schedule or entry["schedule"])
    deliver = (deliver or entry["deliver"] or "origin").strip()
    if deliver not in _deliver_options():
        return {"error": f"'{deliver}' is not a delivery target on this instance"}
    prompt_text = (prompt if prompt is not None else entry["prompt"]) or ""
    prompt_text = prompt_text.strip()
    if not prompt_text and not entry["noAgent"]:
        return {"error": "the focus/instructions text cannot be empty"}
    written = _write_config(entry["config"], config or {})

    from cron import jobs as cron_jobs
    existing = _job_for(name)
    if existing:
        updates: Dict[str, Any] = {"schedule": expr, "prompt": prompt_text, "deliver": deliver}
        if model is not None:
            updates["model"] = model or None
        job = cron_jobs.update_job(existing["id"], updates) or existing
    else:
        spec = _bp().parse_blueprint(Path(entry["path"]).read_text(encoding="utf-8"))
        if spec is None:
            return {"error": f"blueprint block for '{name}' could not be read"}
        spec = dataclasses.replace(spec, schedule=expr, deliver=deliver,
                                   prompt=prompt_text or spec.prompt,
                                   model=(model if model else spec.model))
        job = _bp().create_blueprint_job(spec, origin=origin)
    _mark_suggestion(name, "accepted")
    fresh = _find_entry(name) or entry
    return {"ok": True, "job": job, "entry": fresh, "configWritten": written}


def unschedule_blueprint(name: str) -> Dict[str, Any]:
    """Remove the job and put the suggestion back to pending so the
    /suggestions list offers it again (the reset the workshop documents)."""
    job = _job_for(name)
    if not job:
        return {"error": f"'{name}' is not scheduled"}
    from cron import jobs as cron_jobs
    cron_jobs.remove_job(job["id"])
    _mark_suggestion(name, "pending")
    return {"ok": True, "removedJobId": job["id"], "entry": _find_entry(name)}


def _mark_suggestion(name: str, status: str) -> None:
    sug = _suggestion_for(name)
    if not sug or sug.get("status") == status or sug.get("status") == "dismissed":
        return
    try:
        from cron import suggestions as cs
        cs._set_status(sug["id"], status)
    except Exception:
        logger.debug("could not mark suggestion %s as %s", name, status, exc_info=True)


# ---------------------------------------------------------------------------
# input files — read/write the files a blueprint reads, from the form
# ---------------------------------------------------------------------------

MAX_FILE_BYTES = 512 * 1024


def _safe_path(raw: str) -> Path:
    """Expand and confine a user-supplied path to the home directory,
    keeping Hermes' own state and SSH material off limits."""
    raw = str(raw or "").strip()
    if not raw:
        raise ValueError("a path is required")
    home = Path.home().resolve()
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = home / p
    p = p.resolve()
    if p != home and home not in p.parents:
        raise ValueError("only files under your home folder can be edited here")
    for forbidden in (".hermes", ".ssh", ".gnupg", ".aws", ".config"):
        if (home / forbidden) == p or (home / forbidden) in p.parents:
            raise ValueError(f"~/{forbidden} is not editable from here")
    return p


def read_input(path: str) -> Dict[str, Any]:
    """Describe a file (content) or a folder (its files) at ``path``."""
    p = _safe_path(path)
    out: Dict[str, Any] = {"path": str(p), "display": _display(p), "exists": p.exists()}
    if p.is_dir():
        entries = []
        for child in sorted(p.rglob("*")):
            if child.is_file() and not child.name.startswith("."):
                rel = child.relative_to(p).as_posix()
                if rel.count("/") > 2:
                    continue
                try:
                    st = child.stat()
                    entries.append({"name": rel, "size": st.st_size, "mtime": st.st_mtime})
                except OSError:
                    continue
        out.update({"kind": "dir", "files": entries[:200]})
        return out
    out["kind"] = "file"
    if p.exists():
        try:
            raw = p.read_bytes()
        except OSError as exc:
            raise ValueError(f"cannot read {p.name}: {exc}")
        out["truncated"] = len(raw) > MAX_FILE_BYTES
        out["content"] = raw[:MAX_FILE_BYTES].decode("utf-8", errors="replace")
    else:
        out["content"] = ""
    return out


def write_input(path: str, content: str) -> Dict[str, Any]:
    p = _safe_path(path)
    if p.is_dir():
        raise ValueError(f"{_display(p)} is a folder — pick a file inside it")
    data = str(content or "")
    if len(data.encode("utf-8")) > MAX_FILE_BYTES:
        raise ValueError("file is too large to save from here (512KB limit)")
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(data, encoding="utf-8")
    tmp.replace(p)
    return {"ok": True, "path": str(p), "display": _display(p), "bytes": len(data.encode("utf-8"))}


def _display(p: Path) -> str:
    try:
        return "~/" + p.resolve().relative_to(Path.home().resolve()).as_posix()
    except ValueError:
        return str(p)
