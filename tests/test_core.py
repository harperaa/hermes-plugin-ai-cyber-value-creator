"""Unit tests for the ai-cyber-value-creator plugin core.

Run from the repo root:  python3 -m pytest tests/ -q
The plugin is loaded as a package from the repo root so relative imports work
exactly as they do under the hermes plugin manager.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PKG = "acvc_test_pkg"


def _load_pkg():
    if PKG in sys.modules:
        return sys.modules[PKG]
    spec = importlib.util.spec_from_file_location(
        PKG, ROOT / "__init__.py", submodule_search_locations=[str(ROOT)]
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[PKG] = mod
    spec.loader.exec_module(mod)
    return mod


_load_pkg()
methodology = importlib.import_module(f"{PKG}.methodology")
context_store = importlib.import_module(f"{PKG}.context_store")
progress = importlib.import_module(f"{PKG}.progress")
tools = importlib.import_module(f"{PKG}.tools")
commands = importlib.import_module(f"{PKG}.commands")


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    yield tmp_path


# ---------------------------------------------------------------------------
# Methodology model
# ---------------------------------------------------------------------------

def test_phase_and_task_counts():
    assert len(methodology.ALL_PHASES) == 5
    assert methodology.ALL_PHASES[0].foundation is True
    assert len(methodology.ALL_PHASES[0].tasks) == 5
    for p in methodology.ROADMAP_PHASES:
        assert len(p.tasks) == 3
    assert len(methodology.ALL_TASK_IDS) == 17
    assert len(set(methodology.ALL_TASK_IDS)) == 17


def test_phase_for_task_and_titles():
    phase, task = methodology.phase_for_task("create-value-icp")
    assert phase.id == "create-value"
    assert methodology.step_task_title(phase, task) == "Create Value: Get Clarity on the ICP"
    assert methodology.phase_for_task("nope") is None


def test_flywheel_colors_and_gates():
    by_id = {p.id: p for p in methodology.ROADMAP_PHASES}
    assert by_id["attract"].color == "#ec4899"
    assert by_id["nurture"].color == "#f59e0b"
    assert by_id["convert"].color == "#22c55e"
    assert by_id["deliver"].color == "#3b82f6"
    assert [p.gate_to_next for p in methodology.ROADMAP_PHASES] == [
        "Leads", "Trust", "Sales", "Testimonials",
    ]


def test_brief_foundation_vs_flywheel():
    phase, task = methodology.phase_for_task("create-value-icp")
    brief = methodology.build_task_description(phase, task, context_dir="/tmp/x")
    assert "run this step yourself, directly with the user" in brief
    assert "record_company_context" in brief
    assert "Do NOT delegate ANY part" in brief
    assert "/tmp/x/company-context.md" in brief

    phase2, task2 = methodology.phase_for_task("attract-referral")
    brief2 = methodology.build_task_description(phase2, task2)
    assert "Search the available skills FIRST" in brief2
    assert "delegate ANY part" not in brief2


def test_next_status_cycle():
    assert methodology.next_status("todo") == "in-progress"
    assert methodology.next_status("in-progress") == "done"
    assert methodology.next_status("done") == "todo"


# ---------------------------------------------------------------------------
# Company context
# ---------------------------------------------------------------------------

def test_context_render_parse_roundtrip():
    c = {
        "icp": "Mid-market CISOs in healthcare",
        "problems": "| Problem | Score |\n|---|---|\n| Ransomware | 9 |",
        "solutions": "1. vCISO service\n2. Tabletop exercises",
        "offer": "### The 90-Day Security Sprint\n\n**Price:** $15k",
        "elevatorPitch": "I help CISOs sleep at night within 90 days.",
    }
    md = context_store.render_company_context_body(c)
    parsed = context_store.parse_company_context_file(md)
    assert parsed["icp"] == c["icp"]
    assert "Ransomware" in parsed["problems"]
    assert "vCISO" in parsed["solutions"]
    assert "90-Day Security Sprint" in parsed["offer"]
    assert parsed["elevatorPitch"] == c["elevatorPitch"]


def test_parse_placeholders_dropped():
    md = context_store.render_company_context_body({})
    parsed = context_store.parse_company_context_file(md)
    assert parsed == {}


def test_parse_confirmed_context_folds_into_icp():
    md = (
        "# Company Context\n\n## Ideal Customer Profile\n\nCISOs\n\n"
        "## Confirmed Context\n\nNiche: wealth\n"
    )
    parsed = context_store.parse_company_context_file(md)
    assert "CISOs" in parsed["icp"]
    assert "### Confirmed Context" in parsed["icp"]
    assert "Niche: wealth" in parsed["icp"]


def test_parse_deep_headers_stay_in_section():
    md = "## Active Offer\n\nIntro\n\n### Value Stack\n\n- a\n- b\n"
    parsed = context_store.parse_company_context_file(md)
    assert "Value Stack" in parsed["offer"]


def test_apply_and_merge_context():
    context_store.apply_company_context({"icp": "CISOs", "junk": "x"})
    ctx = context_store.get_company_context()
    assert ctx["icp"] == "CISOs"
    assert "junk" not in ctx
    assert ctx.get("updatedAt")
    # The shared file was written and merges back.
    assert context_store.context_file_path().exists()
    merged = context_store.merged_context()
    assert merged["icp"] == "CISOs"


def test_file_fills_gaps_but_state_wins():
    context_store.apply_company_context({"icp": "From state"})
    context_store.context_file_path().write_text(
        "## Ideal Customer Profile\n\nFrom file\n\n## Their Problems\n\nFile problems\n",
        encoding="utf-8",
    )
    merged = context_store.merged_context()
    assert merged["icp"] == "From state"
    assert merged["problems"] == "File problems"


def test_summarize_offer():
    md = (
        "The active offer is **The Sprint** now.\n\n"
        "**Positioning line:** Security in 90 days.\n\n**Price:** $15k\n"
    )
    s = context_store.summarize_offer(md)
    assert "**The Sprint** — Security in 90 days." in s
    assert "**Price:** $15k" in s
    assert context_store.summarize_offer("") is None
    assert context_store.summarize_offer("Just a paragraph.\n\nMore.") == "Just a paragraph."


# ---------------------------------------------------------------------------
# Progress + status derivation (kanban mocked out)
# ---------------------------------------------------------------------------

def test_progress_store_roundtrip():
    progress.mark_step_status("create-value-icp", "in-progress")
    p = progress.get_progress()
    assert p["create-value-icp"]["status"] == "in-progress"
    progress.mark_step_status("create-value-icp", "done")
    assert progress.get_progress()["create-value-icp"]["status"] == "done"
    progress.reset_progress()
    assert progress.get_progress() == {}
    assert progress.get_task_links() == {}


def test_step_status_from_kanban_rules():
    f = progress._step_status_from_kanban
    assert f("done", "todo") == "done"
    assert f("done", "in-progress") == "done"
    assert f("running", "todo") == "in-progress"
    assert f("ready", "todo") == "in-progress"
    assert f("archived", "todo") == "todo"
    assert f(None, "todo") == "todo"
    assert f("running", "done") == "done"


def test_roadmap_data_shape():
    data = progress.roadmap_data()
    assert data["totalTasks"] == 17
    assert data["doneTasks"] == 0
    assert len(data["phases"]) == 5
    foundation = data["phases"][0]
    assert foundation["foundation"] is True
    assert foundation["totalCount"] == 5
    task = foundation["tasks"][0]
    assert set(task) >= {"id", "title", "blurb", "status", "kanban"}


def test_find_step_for_kanban_task():
    links = {"create-value-icp": {"kanbanTaskId": "abc123"}}
    progress.set_task_links(links)
    assert progress.find_step_for_kanban_task("abc123") == "create-value-icp"
    assert progress.find_step_for_kanban_task("nope") is None


# ---------------------------------------------------------------------------
# Tools (handlers must return JSON strings and never raise)
# ---------------------------------------------------------------------------

def test_record_and_get_company_context_tools():
    out = json.loads(tools.record_company_context({"field": "icp", "content": "CISOs"}))
    assert out["ok"] is True
    out = json.loads(tools.get_company_context({}))
    assert out["context"]["icp"] == "CISOs"

    bad = json.loads(tools.record_company_context({"field": "bogus", "content": "x"}))
    assert "error" in bad
    bad = json.loads(tools.record_company_context({"field": "icp", "content": "  "}))
    assert "error" in bad


def test_value_creator_status_tool():
    out = json.loads(tools.value_creator_status({}))
    assert out["totalTasks"] == 17
    assert out["foundationComplete"] is False
    assert out["nextStep"]["id"] == "create-value-icp"


def test_start_value_step_unknown_id():
    out = json.loads(tools.start_value_step({"step_id": "bogus"}))
    assert "error" in out


def test_slash_commands():
    text = commands.handle_value_creator("")
    assert "AI Cyber Value Creator™ roadmap" in text
    assert "create-value-icp" in text
    usage = commands.handle_value_step("")
    assert usage.startswith("Usage:")
    unknown = commands.handle_value_step("bogus")
    assert "Unknown step id" in unknown


# ---------------------------------------------------------------------------
# register(ctx) wiring against a fake PluginContext
# ---------------------------------------------------------------------------

class FakeCtx:
    def __init__(self):
        self.tools = {}
        self.commands = {}
        self.skills = {}
        self.hooks = {}

    def register_tool(self, name, toolset, schema, handler, **kw):
        assert schema["name"] == name
        self.tools[name] = (toolset, schema, handler)

    def register_command(self, name, handler, description="", args_hint=""):
        self.commands[name] = handler

    def register_skill(self, name, path, description=""):
        assert Path(path).exists()
        self.skills[name] = path

    def register_hook(self, hook_name, callback):
        self.hooks.setdefault(hook_name, []).append(callback)


def test_register_wires_everything():
    pkg = sys.modules[PKG]
    ctx = FakeCtx()
    pkg.register(ctx)
    assert set(ctx.tools) == {
        "record_company_context", "get_company_context",
        "value_creator_status", "start_value_step",
        "ask_user_question",
    }
    assert set(ctx.commands) == {"value-creator", "value-step"}
    assert {
        "ai-cyber-value-creator-playbook", "define-icp", "research-problems",
        "build-solutions", "craft-offer", "craft-elevator-pitch", "company-context",
    } <= set(ctx.skills)
    assert set(ctx.hooks) == {
        "kanban_task_claimed", "kanban_task_completed", "kanban_task_blocked",
    }


def test_kanban_hook_updates_progress():
    pkg = sys.modules[PKG]
    ctx = FakeCtx()
    pkg.register(ctx)
    progress.set_task_links({"attract-referral": {"kanbanTaskId": "kb1"}})
    for cb in ctx.hooks["kanban_task_completed"]:
        cb(task_id="kb1", profile_name="default")
    assert progress.get_progress()["attract-referral"]["status"] == "done"
    # Unknown task ids are ignored without raising.
    for cb in ctx.hooks["kanban_task_completed"]:
        cb(task_id="unknown", profile_name="default")
