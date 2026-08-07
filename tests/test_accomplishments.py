"""Accomplishments aggregator — the acvc plugin collects each sibling
plugin's ACHIEVEMENT + achievements_progress() and enforces its own
roadmap rule (ALL steps done for credit)."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    return tmp_path


def _load_plugin_api():
    name = "acvc_api_accomplish_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "dashboard" / "plugin_api.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_roadmap_requires_every_step(home, monkeypatch):
    api = _load_plugin_api()

    def fake_core():
        prog = types.SimpleNamespace(roadmap_data=lambda: {
            "phases": [
                {"id": "found", "title": "Foundation",
                 "tasks": [{"status": "done"}, {"status": "done"}]},
                {"id": "attract", "title": "Attract",
                 "tasks": [{"status": "done"}, {"status": "todo"}]},
            ]})
        return None, None, prog

    monkeypatch.setattr(api, "_core", fake_core)
    out = api.achievements_progress()
    assert out["complete"] is False           # one step short = no credit
    assert out["items"][0]["done"] is True
    assert "1/2" in out["items"][1]["label"]

    def all_done():
        prog = types.SimpleNamespace(roadmap_data=lambda: {
            "phases": [{"id": "f", "title": "F",
                        "tasks": [{"status": "done"}]}]})
        return None, None, prog

    monkeypatch.setattr(api, "_core", all_done)
    assert api.achievements_progress()["complete"] is True


def test_aggregator_collects_siblings_and_skips_broken(home, monkeypatch,
                                                       tmp_path):
    api = _load_plugin_api()
    fake_root = tmp_path / "plugins"
    good = fake_root / "good-plugin" / "dashboard"
    good.mkdir(parents=True)
    (good / "plugin_api.py").write_text(
        'ACHIEVEMENT = {"id": "g", "name": "Good", "icon": "*",\n'
        '               "description": "d"}\n'
        "def achievements_progress():\n"
        '    return {"items": [{"id": "x", "label": "X", "done": True}],\n'
        '            "complete": True}\n')
    broken = fake_root / "broken-plugin" / "dashboard"
    broken.mkdir(parents=True)
    (broken / "plugin_api.py").write_text("raise RuntimeError('boom')\n")
    own = fake_root / "ai-cyber-value-creator"
    own.mkdir()

    monkeypatch.setattr(api, "_PLUGIN_ROOT", own)
    out = api._sibling_progress()
    assert list(out) == ["good-plugin"]        # broken sibling skipped
    assert out["good-plugin"]["complete"] is True
    assert out["good-plugin"]["name"] == "Good"
