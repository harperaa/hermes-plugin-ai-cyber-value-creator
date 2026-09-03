"""Weekly feedback client tests — freshness, payload assembly, submission."""
from __future__ import annotations

import importlib
import importlib.util
import json
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

PKG = "acvc_fb_test_pkg"
ROOT = Path(__file__).resolve().parent.parent

if PKG not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        PKG, str(ROOT / "__init__.py"),
        submodule_search_locations=[str(ROOT)])
    mod = importlib.util.module_from_spec(spec)
    sys.modules[PKG] = mod
    spec.loader.exec_module(mod)

feedback = importlib.import_module(f"{PKG}.feedback")
progress = importlib.import_module(f"{PKG}.progress")
coach = importlib.import_module(f"{PKG}.coach")


@pytest.fixture()
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    monkeypatch.setenv("FEEDBACK_HUB_URL", "https://hub.example.com/ingest")
    monkeypatch.setenv("FEEDBACK_HUB_TOKEN", "tok-123")
    return tmp_path


def test_freshness_thresholds():
    now = 1_000_000_000.0
    assert feedback.freshness(None, now) == "yellow"
    assert feedback.freshness(now - 3 * 86400, now) == "green"
    assert feedback.freshness(now - 7 * 86400, now) == "green"
    assert feedback.freshness(now - 8 * 86400, now) == "yellow"
    assert feedback.freshness(now - 14 * 86400, now) == "yellow"
    assert feedback.freshness(now - 15 * 86400, now) == "red"


def test_phase_schedule():
    """Steady green for 5 days, flashing green days 6-7, flashing yellow
    8-14, flashing red 15+; never-submitted counts as late."""
    now = time.time()
    d = 86400
    assert feedback.phase(None, now) == "late"
    assert feedback.phase(now, now) == "steady"
    assert feedback.phase(now - 5 * d, now) == "steady"
    assert feedback.phase(now - 5 * d - 1, now) == "due"
    assert feedback.phase(now - 7 * d, now) == "due"
    assert feedback.phase(now - 7 * d - 1, now) == "late"
    assert feedback.phase(now - 14 * d, now) == "late"
    assert feedback.phase(now - 14 * d - 1, now) == "overdue"
    assert feedback.phase(now - 40 * d, now) == "overdue"


def test_status_unconfigured(home, monkeypatch):
    monkeypatch.delenv("FEEDBACK_HUB_URL")
    st = feedback.status()
    assert st["configured"] is False


def test_submit_requires_everything(home):
    kw = {"name": "Al Mentee", "email": "m@x.com"}
    assert "name" in feedback.submit("green", "n", "a", "s", True,
                                     name="", email="m@x.com")["error"]
    assert "email" in feedback.submit("green", "n", "a", "s", True,
                                      name="Al", email="nope")["error"]
    assert "traffic light" in feedback.submit("", "n", "a", "s", True, **kw)["error"]
    assert "required" in feedback.submit("green", "n", "a", "s", False, **kw)["error"]
    assert "note" in feedback.submit("green", "", "a", "s", True, **kw)["error"]
    assert "activities" in feedback.submit("green", "n", "", "s", True, **kw)["error"]
    assert "next step" in feedback.submit("green", "n", "a", "s", True,
                                          next_step="", **kw)["error"]


def test_submit_assembles_and_posts(home):
    # seed mentee identity + level + roadmap state
    (home / "mentor-auth.json").write_text(json.dumps(
        {"email": "mentee@example.com", "password_hash": "x"}))
    vcl = home / "value-creator-level"
    vcl.mkdir(parents=True)
    (vcl / "state.json").write_text(json.dumps({
        "level": 2,
        "badges": [{"level": 2, "name": "The Listener", "emoji": "👂"}],
        "assessment": "Solid listener, thin on metrics.",
        "checklist": {"targetLevel": 3, "createdAt": 1756000000, "items": [
            {"id": "rx-1", "status": "done", "text": "Interview 5 ICP buyers",
             "advice": "Use the 3-question script", "references": ["Mom Test ch.2"],
             "challenge": "Name the 5", "proof": "call notes", "evidence": "5 notes attached",
             "attempts": 1},
            {"id": "rx-2", "status": "open", "text": "Publish 3 posts",
             "advice": "One insight per post", "references": [], "proof": "links"}]},
        "history": [{"at": 1756100000, "level": 2, "mode": "exam", "rationale": "Clear ICP",
                     "strengths": ["specific"], "gaps": ["no metrics"],
                     "ladders": {"security": {"rung": 2, "misses": [], "retried": 0}},
                     "transcript": [{"role": "examiner", "text": "What are you building?"},
                                    {"role": "mentee", "text": "A vCISO offer for MSPs"}]}],
    }))
    progress.mark_step_status("create-value-icp", "done")
    # a coach chat thread on that step — must travel with the report
    cst = coach.load_state()
    cst["steps"]["create-value-icp"] = {"status": "done", "summary": "Mid-market MSPs",
        "messages": [{"role": "coach", "text": "Who exactly do you serve?"},
                     {"role": "mentee", "text": "MSPs with 20-200 seats"}]}
    coach.save_state(cst)

    sent = {}

    class FakeResp:
        def read(self):
            return b'{"ok": true}'

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_open(req, timeout=0):
        sent["url"] = req.full_url
        sent["auth"] = req.get_header("Authorization")
        sent["payload"] = json.loads(req.data.decode())
        return FakeResp()

    with patch.object(feedback.urllib.request, "urlopen", fake_open):
        r = feedback.submit("yellow", "solid week", "shipped funnel",
                            "stuck on ads", True,
                            name="Al Mentee", email="mentee@example.com",
                            next_step="call two more brokers")
    assert r["ok"], r
    p = sent["payload"]
    assert sent["url"] == "https://hub.example.com/ingest"
    assert sent["auth"] == "Bearer tok-123"
    assert p["email"] == "mentee@example.com"
    assert p["name"] == "Al Mentee"
    assert p["previousEmail"] == ""   # first submission — nothing to migrate
    assert p["sentiment"] == "yellow"
    assert p["stuck"] == "stuck on ads"
    assert p["level"] == 2 and p["levelName"] == "The Listener"
    assert p["checklistDone"] == 1 and p["checklistTotal"] == 2
    assert p["roadmapDone"] == 1 and p["roadmapTotal"] == 17
    assert p["statusAck"] is True
    # local state updated -> pill goes green, clock restarts (steady)
    st = feedback.status()
    assert st["freshness"] == "green"
    assert st["phase"] == "steady"
    assert st["logCount"] == 1
    # the log keeps everything that was sent, dossier included
    lg = feedback.logs()
    assert lg["count"] == 1
    e = lg["entries"][0]
    assert e["sentiment"] == "yellow" and e["nextStep"] == "call two more brokers"
    assert e["level"] == 2 and e["roadmapDone"] == 1
    assert e["detail"]["level"]["level"] == 2
    # everything the level plugin knows travels: assessment, verdicts with
    # the examiner transcript + ladders, and the prescription verbatim
    lv = e["detail"]["level"]
    assert lv["assessment"] == "Solid listener, thin on metrics."
    v = lv["verdicts"][0]
    assert v["rationale"] == "Clear ICP" and v["ladders"]["security"]["rung"] == 2
    assert v["transcript"][1] == {"role": "mentee", "text": "A vCISO offer for MSPs"}
    rx = lv["prescription"]
    assert rx["targetLevel"] == 3 and len(rx["items"]) == 2
    assert rx["items"][0]["advice"] == "Use the 3-question script"
    assert rx["items"][0]["references"] == ["Mom Test ch.2"]
    assert rx["items"][0]["evidence"] == "5 notes attached"
    assert rx["items"][1]["status"] == "open"
    # roadmap: every step with its coach chat thread
    steps = e["detail"]["roadmap"]["steps"]
    icp = [s for s in steps if s["id"] == "create-value-icp"][0]
    assert icp["progress"] == "done" and icp["summary"] == "Mid-market MSPs"
    assert icp["thread"][1] == {"role": "mentee", "text": "MSPs with 20-200 seats"}
    assert e["detail"]["roadmap"]["companyContext"] is not None
    assert any(s.get("id") == "create-value-icp" or s.get("step") == "create-value-icp"
               for s in e["detail"]["roadmap"].get("steps", []))
    assert e["at"] == st["lastSubmittedAt"]


def test_submit_surfaces_hub_errors(home):
    def boom(req, timeout=0):
        raise feedback.urllib.error.URLError("connection refused")

    with patch.object(feedback.urllib.request, "urlopen", boom):
        r = feedback.submit("green", "n", "a", "s", True,
                            name="Al", email="m@x.com", next_step="x")
    assert "could not reach" in r["error"]
    assert feedback.status()["freshness"] == "yellow"   # not recorded


def test_identity_saved_and_email_edit_migrates(home):
    sent = {}

    class FakeResp:
        def read(self):
            return b'{"ok": true}'

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_open(req, timeout=0):
        sent["payload"] = json.loads(req.data.decode())
        return FakeResp()

    with patch.object(feedback.urllib.request, "urlopen", fake_open):
        feedback.submit("green", "n", "a", "s", True,
                        name="Al Mentee", email="old@x.com", next_step="x")
    ident = feedback.get_identity()
    assert ident == {"name": "Al Mentee", "email": "old@x.com"}
    assert feedback.status()["identity"]["email"] == "old@x.com"

    # editing the email carries previousEmail so the hub re-keys records
    with patch.object(feedback.urllib.request, "urlopen", fake_open):
        feedback.submit("green", "n", "a", "s", True,
                        name="Al Mentee", email="new@x.com", next_step="x")
    assert sent["payload"]["previousEmail"] == "old@x.com"
    assert feedback.get_identity()["email"] == "new@x.com"


def test_detail_dossier_and_ssl_guard(home, monkeypatch):
    import importlib
    coach = importlib.import_module(f"{PKG}.coach")
    context_store = importlib.import_module(f"{PKG}.context_store")
    # level state with closed+open items and a verdict
    vcl = home / "value-creator-level"
    vcl.mkdir(parents=True, exist_ok=True)
    (vcl / "state.json").write_text(json.dumps({
        "level": 1,
        "badges": [{"level": 1, "name": "The Spark", "emoji": "🔥"}],
        "history": [{"level": 1, "rationale": "r", "securityNotes": "sn",
                     "ladders": {"ai": {"rung": 1, "misses": 0}}}],
        "checklist": {"targetLevel": 2, "items": [
            {"id": "L2-1", "text": "did it", "proof": "p", "status": "done",
             "evidence": "the receipts", "attempts": 1, "challenge": "q?"},
            {"id": "L2-2", "text": "todo", "proof": "p", "status": "open",
             "attempts": 0},
        ]}}))
    # a coach thread
    cst = coach.load_state()
    cst["steps"]["create-value-icp"] = {
        "status": "active", "summary": "",
        "messages": [{"role": "coach", "text": "Who do you serve?"},
                     {"role": "mentee", "text": "Texas law firms"}],
        "startedAt": 1, "completedAt": None}
    coach.save_state(cst)
    context_store.apply_company_context({"icp": "Texas law firms"})

    sent = {}

    class FakeResp:
        def read(self):
            return b'{"ok": true}'

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_open(req, timeout=0):
        sent["payload"] = json.loads(req.data.decode())
        return FakeResp()

    with patch.object(feedback.urllib.request, "urlopen", fake_open):
        # stuck is optional — blank means "not stuck"
        r = feedback.submit("green", "n", "a", "", True,
                            name="Al", email="m@x.com", next_step="x")
    assert r["ok"], r
    assert sent["payload"]["stuck"] == ""
    d = sent["payload"]["detail"]
    assert d["level"]["closedItems"][0]["evidence"] == "the receipts"
    assert d["level"]["openItems"][0]["id"] == "L2-2"
    assert d["level"]["verdicts"][0]["securityNotes"] == "sn"
    icp = [s2 for s2 in d["roadmap"]["steps"] if s2["id"] == "create-value-icp"][0]
    assert icp["thread"][1]["text"] == "Texas law firms"
    assert d["roadmap"]["companyContext"]["icp"] == "Texas law firms"

    # SSL guard: plain http to a non-local host is refused
    monkeypatch.setenv("FEEDBACK_HUB_URL", "http://evil.example.com/ingest")
    r = feedback.submit("green", "n", "a", "s", True, name="Al", email="m@x.com",
                        next_step="x")
    assert "https" in r["error"]
