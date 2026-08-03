"""Roadmap Coach engine tests — scripted mock LLM, no network.

Covers: start/reply/complete lifecycle, the company-context write +
ambient-profile mirror on foundation completion, flywheel summary storage,
turn gates, and per-step reset (conversation, progress, context field).
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PKG = "acvc_coach_test_pkg"
ROOT = Path(__file__).resolve().parent.parent

if PKG not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        PKG, str(ROOT / "__init__.py"),
        submodule_search_locations=[str(ROOT)])
    mod = importlib.util.module_from_spec(spec)
    sys.modules[PKG] = mod
    spec.loader.exec_module(mod)

coach = importlib.import_module(f"{PKG}.coach")
context_store = importlib.import_module(f"{PKG}.context_store")
progress = importlib.import_module(f"{PKG}.progress")


@pytest.fixture()
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    return tmp_path


@pytest.fixture()
def scripted():
    queue: list[dict] = []

    def fake(instructions, payload, schema, temperature=0.4):
        fake.calls.append((instructions, payload))
        return queue.pop(0)

    fake.calls = []
    with patch.object(coach, "_structured", fake):
        yield queue, fake


def test_guidance_covers_every_task():
    meth = importlib.import_module(f"{PKG}.methodology")
    missing = [t.id for p in meth.ALL_PHASES for t in p.tasks
               if not coach.GUIDANCE.get(t.id)]
    assert not missing, missing


def test_foundation_complete_writes_context_and_profile(home, scripted):
    queue, _ = scripted
    queue[:] = [{"reply": "Who are you trying to serve?"}]
    r = coach.start("create-value-icp")
    assert r["ok"] and r["step"]["messages"][0]["role"] == "coach"
    assert progress.get_progress().get("create-value-icp", {}).get("status") == "in-progress"

    queue[:] = [{"action": "reply", "reply": "Which of the six dimensions?"}]
    r = coach.answer("create-value-icp", "Cybersecurity founders")
    assert r["action"] == "reply"

    queue[:] = [{"action": "complete",
                 "summary": "ICP confirmed: US-based solo cybersecurity consultants.",
                 "contextValue": "US-based solo cybersecurity consultants, "
                                 "1-5 years out on their own, serving SMBs."}]
    r = coach.answer("create-value-icp", "Yes, confirmed — that's my ICP.")
    assert r["action"] == "complete"
    assert r["step"]["status"] == "complete"

    ctx = context_store.merged_context()
    assert "solo cybersecurity consultants" in ctx["icp"]
    assert progress.get_progress()["create-value-icp"]["status"] == "done"
    profile = (home / "memories" / "USER.md").read_text()
    assert "Company Context (auto-updated" in profile
    assert "solo cybersecurity consultants" in profile


def test_flywheel_complete_stores_summary_no_context(home, scripted):
    queue, _ = scripted
    queue[:] = [{"reply": "Who already trusts you?"}]
    coach.start("attract-referral")
    queue[:] = [{"action": "reply", "reply": "Name three."}]
    coach.answer("attract-referral", "My old employer's partner network")
    queue[:] = [{"action": "complete",
                 "summary": "Committed to weekly touches with 4 named partners."}]
    r = coach.answer("attract-referral", "Yes — locked in.")
    assert r["action"] == "complete"
    st = coach.public_state()["steps"]["attract-referral"]
    assert st["status"] == "complete"
    assert "4 named partners" in st["summary"]
    assert context_store.merged_context().get("icp") in (None, "")


def test_min_turn_gate_in_prompt(home, scripted):
    queue, fake = scripted
    queue[:] = [{"reply": "Q"}]
    coach.start("create-value-icp")
    queue[:] = [{"action": "reply", "reply": "next"}]
    coach.answer("create-value-icp", "first answer")
    assert "Too early to complete" in fake.calls[-1][0]


def test_max_turns_force_complete(home, scripted):
    queue, _ = scripted
    queue[:] = [{"reply": "Q"}]
    coach.start("attract-tribe")
    for i in range(coach.MAX_TURNS - 1):
        queue[:] = [{"action": "reply", "reply": "more"}]
        coach.answer("attract-tribe", f"a{i}")
    # model tries to keep replying — engine completes anyway
    queue[:] = [{"action": "reply", "reply": "one more?", "summary": ""}]
    r = coach.answer("attract-tribe", "final")
    assert r["action"] == "complete"


def test_reset_clears_conversation_progress_and_context(home, scripted):
    queue, _ = scripted
    queue[:] = [{"reply": "Q"}]
    coach.start("create-value-icp")
    queue[:] = [{"action": "reply", "reply": "next"}]
    coach.answer("create-value-icp", "a1")
    queue[:] = [{"action": "complete", "summary": "s", "contextValue": "The ICP"}]
    coach.answer("create-value-icp", "confirmed")
    assert context_store.merged_context().get("icp") == "The ICP"

    r = coach.reset("create-value-icp")
    assert r["ok"]
    st = coach.public_state()["steps"]["create-value-icp"]
    assert st["status"] == "open" and st["messages"] == []
    assert not (context_store.merged_context().get("icp") or "").strip()
    assert progress.get_progress()["create-value-icp"]["status"] == "todo"
    profile = (home / "memories" / "USER.md").read_text()
    assert "The ICP" not in profile


def test_unknown_task_rejected(home, scripted):
    assert coach.start("bogus-step")["error"]
    assert coach.reset("bogus-step")["error"]


def test_coach_error_lets_mentee_resend(home, scripted):
    queue, fake = scripted
    queue[:] = [{"reply": "Q"}]
    coach.start("create-value-icp")

    def boom(*a, **k):
        raise RuntimeError("coach returned no usable JSON")

    with patch.object(coach, "_structured", boom):
        r = coach.answer("create-value-icp", "my answer")
    assert "coach unavailable" in r["error"]
    # the failed answer must NOT be stuck in the transcript
    st = coach.public_state()["steps"]["create-value-icp"]
    assert all(m["text"] != "my answer" for m in st["messages"])
