"""Shared Company Context + plugin state storage.

Everything lives in the plugin's data directory
(``$HERMES_HOME/plugins-data/ai-cyber-value-creator/``):

* ``state.json``      — step progress, kanban task links, context fields
* ``company-context.md`` — the human-readable snapshot agents read/write

Ported from the paperclip worker's company-context engine (render / parse /
summarize / merge). The markdown file is the always-available channel; the
structured state is what the dashboard edits.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path

from .methodology import (
    CONTEXT_FIELDS,
    CONTEXT_FIELD_KEYS,
    CONTEXT_FILE_NAME,
    ELEVATOR_PITCH_KEY,
    ELEVATOR_PITCH_LABEL,
)

_LOCK = threading.Lock()


def get_hermes_home() -> Path:
    val = (os.environ.get("HERMES_HOME") or "").strip()
    return Path(val) if val else Path.home() / ".hermes"


def get_data_dir() -> Path:
    d = get_hermes_home() / "plugins-data" / "ai-cyber-value-creator"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _state_path() -> Path:
    return get_data_dir() / "state.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_state() -> dict:
    try:
        with open(_state_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    return {}


def save_state(state: dict) -> None:
    path = _state_path()
    with _LOCK:
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".state-", suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, sort_keys=True)
            os.replace(tmp, path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise


# ---------------------------------------------------------------------------
# Company context
# ---------------------------------------------------------------------------

def get_company_context() -> dict:
    ctx = load_state().get("context")
    return dict(ctx) if isinstance(ctx, dict) else {}


def render_company_context_body(c: dict) -> str:
    """Human-readable snapshot written to company-context.md."""
    lines = ["# Company Context — who we serve & what we deliver", ""]
    for f in CONTEXT_FIELDS:
        v = c.get(f["key"])
        lines += [
            f"## {f['label']}",
            "",
            v.strip() if isinstance(v, str) and v.strip()
            else "_Not yet defined — to be discovered in the Create Value foundation._",
            "",
        ]
    pitch = c.get(ELEVATOR_PITCH_KEY)
    lines += [
        f"## {ELEVATOR_PITCH_LABEL}",
        "",
        pitch.strip() if isinstance(pitch, str) and pitch.strip()
        else "_Generated from the fields above once the foundation is complete._",
        "",
    ]
    if c.get("updatedAt"):
        lines.append(f"_Last updated: {c['updatedAt']}_")
    return "\n".join(lines)


def context_file_path() -> Path:
    return get_data_dir() / CONTEXT_FILE_NAME


def write_shared_context_file(c: dict) -> None:
    """Best-effort: write the live snapshot so sessions (and tasks) can read it."""
    try:
        context_file_path().write_text(render_company_context_body(c) + "\n", encoding="utf-8")
    except OSError:
        pass  # state.json remains the durable channel


def read_shared_context_file() -> str | None:
    try:
        md = context_file_path().read_text(encoding="utf-8").strip()
        return md or None
    except OSError:
        return None


_HEADER_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")


def _field_for_header(h: str) -> str | None:
    t = h.lower()
    if "elevator" in t or "pitch" in t:
        return ELEVATOR_PITCH_KEY
    if "offer" in t:
        return "offer"
    if "solution" in t:
        return "solutions"
    if "problem" in t:
        return "problems"
    # "Confirmed Context" (niche / outcome / avatar / recognition signal)
    # belongs with the ICP — folded in below.
    if "confirmed context" in t:
        return "_confirmedContext"
    if (
        "ideal customer" in t
        or re.search(r"\bicp\b", t)
        or "avatar" in t
        or "who we serve" in t
    ):
        return "icp"
    return None


def parse_company_context_file(markdown: str) -> dict:
    """Parse company-context.md into structured fields, leniently.

    Only top-level (#/##) headers delimit fields — deeper headers (###+) stay
    in the section body (e.g. the One-Page Offer's subsections).
    """
    out: dict[str, str] = {}
    fld: str | None = None
    buf: list[str] = []

    def flush() -> None:
        nonlocal buf
        if fld and buf:
            text = "\n".join(buf).strip()
            if text and fld not in out:
                out[fld] = text
        buf = []

    for line in markdown.splitlines():
        m = _HEADER_RE.match(line)
        if m and len(m.group(1)) <= 2:
            flush()
            fld = _field_for_header(m.group(2))
            continue
        if fld:
            buf.append(line)
    flush()

    if "_confirmedContext" in out:
        prefix = f"{out['icp']}\n\n" if out.get("icp") else ""
        out["icp"] = f"{prefix}### Confirmed Context\n\n{out['_confirmedContext']}"
        del out["_confirmedContext"]
    # Drop the render placeholders so they don't round-trip as real values.
    for k in list(out):
        if out[k].startswith("_Not yet defined") or out[k].startswith("_Generated from"):
            del out[k]
    return out


def summarize_offer(markdown: str | None) -> str | None:
    """Short, panel-friendly summary of the (potentially long) One-Page Offer."""
    md = (markdown or "").strip()
    if not md:
        return None

    def pick(pattern: str, flags: int = re.IGNORECASE) -> str | None:
        m = re.search(pattern, md, flags)
        return m.group(1).strip() if m else None

    name = pick(r"active offer is\s+\*\*(.+?)\*\*") or pick(r"^###\s+(.+)$", re.MULTILINE)
    positioning = pick(r"\*\*Positioning line:\*\*\s*(.+)")
    price = pick(r"\*\*Price:\*\*\s*(.+)")
    lines: list[str] = []
    if name:
        lines.append(f"**{name}** — {positioning}" if positioning else f"**{name}**")
    elif positioning:
        lines.append(positioning)
    if price:
        lines.append(f"**Price:** {price}")
    if lines:
        return "\n\n".join(lines)
    for para in re.split(r"\n{2,}", md):
        if para.strip():
            return para.strip()
    return None


def apply_company_context(patch: dict) -> dict:
    """Merge string fields from *patch* into the stored context and re-write
    the shared markdown file. Returns the updated context."""
    state = load_state()
    c = state.get("context")
    if not isinstance(c, dict):
        c = {}
    changed = False
    for key in [*CONTEXT_FIELD_KEYS, ELEVATOR_PITCH_KEY]:
        if isinstance(patch.get(key), str):
            c[key] = patch[key]
            changed = True
    if changed:
        c["updatedAt"] = _now_iso()
        state["context"] = c
        save_state(state)
        write_shared_context_file(c)
        try:
            sync_user_profile(c)
        except Exception:
            pass  # ambient mirror must never break a context write
    return c


# ---------------------------------------------------------------------------
# Ambient user profile — hermes injects $HERMES_HOME/memories/USER.md into
# EVERY session's system prompt, so a compact company-context summary there
# makes the whole system aware of who the mentee serves and what they sell.
# One managed entry, rewritten on every context change; other entries (e.g.
# the Value Creator Level one) are left untouched.
# ---------------------------------------------------------------------------

_PROFILE_PREFIX = "Company Context (auto-updated by the ai-cyber-value-creator plugin):"
_PROFILE_DELIM = "\n\u00a7\n"  # tools/memory_tool.ENTRY_DELIMITER


def _first_line(v, limit: int = 110) -> str:
    if not isinstance(v, str) or not v.strip():
        return ""
    return v.strip().splitlines()[0][:limit]


def sync_user_profile(c: dict | None = None) -> None:
    c = c if isinstance(c, dict) else merged_context()
    lines = [_PROFILE_PREFIX]
    pitch = _first_line(c.get(ELEVATOR_PITCH_KEY), 160)
    if pitch:
        lines.append(f"Elevator pitch: {pitch}")
    icp = _first_line(c.get("icp"))
    if icp:
        lines.append(f"ICP: {icp}")
    offer = _first_line(c.get("offer"))
    if offer:
        lines.append(f"Active offer: {offer}")
    if len(lines) == 1:
        lines.append("Not yet defined — the Create Value foundation on the "
                     "Roadmap page discovers it.")
    lines.append("Full detail: the get_company_context tool or "
                 "company-context.md in the plugin data dir.")
    entry = "\n".join(lines)[:600]

    path = get_hermes_home() / "memories" / "USER.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        raw = ""
    entries = [e.strip() for e in raw.split(_PROFILE_DELIM) if e.strip()]
    entries = [e for e in entries if not e.startswith(_PROFILE_PREFIX)]
    entries.append(entry)
    tmp = path.with_suffix(".acvc-tmp")
    tmp.write_text(_PROFILE_DELIM.join(entries) + "\n", encoding="utf-8")
    tmp.replace(path)


def merged_context() -> dict:
    """Structured state merged with fields parsed from the live markdown file
    (manual state wins; the file fills gaps — same rule as the original)."""
    c = get_company_context()
    file_md = read_shared_context_file()
    parsed = parse_company_context_file(file_md) if file_md else {}
    for key in [*CONTEXT_FIELD_KEYS, ELEVATOR_PITCH_KEY]:
        cur = c.get(key)
        if not (isinstance(cur, str) and cur.strip()) and parsed.get(key, "").strip():
            c[key] = parsed[key]
    return c
