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
    assert "stuck" in feedback.submit("green", "n", "a", "", True, **kw)["error"]


def test_submit_assembles_and_posts(home):
    # seed mentee identity + level + roadmap state
    (home / "mentor-auth.json").write_text(json.dumps(
        {"email": "mentee@example.com", "password_hash": "x"}))
    vcl = home / "value-creator-level"
    vcl.mkdir(parents=True)
    (vcl / "state.json").write_text(json.dumps({
        "level": 2,
        "badges": [{"level": 2, "name": "The Listener", "emoji": "👂"}],
        "checklist": {"items": [{"status": "done"}, {"status": "open"}]},
    }))
    progress.mark_step_status("create-value-icp", "done")

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
                            name="Al Mentee", email="mentee@example.com")
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
    # local state updated -> pill goes green
    st = feedback.status()
    assert st["freshness"] == "green"


def test_submit_surfaces_hub_errors(home):
    def boom(req, timeout=0):
        raise feedback.urllib.error.URLError("connection refused")

    with patch.object(feedback.urllib.request, "urlopen", boom):
        r = feedback.submit("green", "n", "a", "s", True,
                            name="Al", email="m@x.com")
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
                        name="Al Mentee", email="old@x.com")
    ident = feedback.get_identity()
    assert ident == {"name": "Al Mentee", "email": "old@x.com"}
    assert feedback.status()["identity"]["email"] == "old@x.com"

    # editing the email carries previousEmail so the hub re-keys records
    with patch.object(feedback.urllib.request, "urlopen", fake_open):
        feedback.submit("green", "n", "a", "s", True,
                        name="Al Mentee", email="new@x.com")
    assert sent["payload"]["previousEmail"] == "old@x.com"
    assert feedback.get_identity()["email"] == "new@x.com"
