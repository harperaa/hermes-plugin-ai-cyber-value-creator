"""Personal Automation gallery — installed blueprints as editable forms."""
from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

PKG = "acvc_automation_test_pkg"
ROOT = Path(__file__).resolve().parent.parent

if PKG not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        PKG, str(ROOT / "__init__.py"), submodule_search_locations=[str(ROOT)])
    mod = importlib.util.module_from_spec(spec)
    sys.modules[PKG] = mod
    spec.loader.exec_module(mod)

automation = importlib.import_module(f"{PKG}.automation")


def _skill(home: Path, name: str, *, schedule: str, prompt: str, level: int,
           config: list | None = None, title: str | None = None) -> None:
    d = home / "skills" / name
    d.mkdir(parents=True)
    lines = ["---", f"name: {name}", f"description: What {name} does.", "version: 1.0.0",
             "metadata:", "  hermes:", f"    tags: [blueprint, level-{level}]"]
    if config:
        lines.append("    config:")
        for c in config:
            first = True
            for k, v in c.items():
                lines.append(("      - " if first else "        ") + f"{k}: {json.dumps(v)}")
                first = False
    lines += ["    blueprint:", f'      schedule: "{schedule}"', "      deliver: origin",
              f'      prompt: "{prompt}"', "      no_agent: false", "---", "",
              f"# {title or name.replace('-', ' ').title()} (Level {level})", "", "Body.", ""]
    (d / "SKILL.md").write_text("\n".join(lines))


@pytest.fixture()
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    monkeypatch.setenv("FEEDBACK_HUB_URL", "")
    (tmp_path / "config.yaml").write_text("skills:\n  config:\n    out_the_door:\n      city: Denver\n")
    _skill(tmp_path, "zeta-extra", schedule="0 8 * * *", prompt="Extra thing.", level=9)
    _skill(tmp_path, "money-watch", schedule="0 */4 * * *", prompt="Watch prices.", level=3)
    _skill(tmp_path, "secure-box-audit", schedule="0 9 1 * *", prompt="Audit the box.", level=0)
    _skill(tmp_path, "out-the-door-brief", schedule="45 6 * * 1-5", prompt="Brief me.", level=2,
           config=[{"key": "out_the_door.city", "default": "", "prompt": "Your city, for the forecast"},
                   {"key": "out_the_door.travel_minutes", "default": "30",
                    "description": "Minutes from door to first commitment"}])
    # discovery must not depend on the host's skills dirs
    monkeypatch.setattr(automation, "_skill_files",
                        lambda: sorted((tmp_path / "skills").glob("*/SKILL.md")))
    return tmp_path


def _names(res):
    return [(e["number"], e["name"]) for e in res["entries"]]


def test_list_orders_curriculum_first_then_others(home):
    res = automation.list_blueprints()
    assert _names(res) == [(1, "secure-box-audit"), (2, "out-the-door-brief"),
                           (3, "money-watch"), (4, "zeta-extra")]
    e = res["entries"][1]
    assert e["title"] == "Out The Door Brief"          # "(Level 2)" stripped
    assert e["level"] == 2 and e["curriculum"] is True
    assert e["scheduleHuman"] == "weekdays at 6:45 am"
    assert e["status"] == "available" and e["job"] is None
    keys = {f["key"]: f for f in e["config"]}
    assert keys["out_the_door.city"]["value"] == "Denver"          # current config wins
    assert keys["out_the_door.travel_minutes"]["value"] == "30"    # default otherwise
    assert keys["out_the_door.city"]["label"] == "Your city, for the forecast"
    assert res["entries"][3]["curriculum"] is False
    assert "origin" in res["deliverOptions"] and "local" in res["deliverOptions"]


def test_describe_schedule_shapes():
    d = automation.describe_schedule
    assert d("0 9 * * *") == "every day at 9:00 am"
    assert d("30 18 * * 1-5") == "weekdays at 6:30 pm"
    assert d("0 7 * * 0") == "every Sunday at 7:00 am"
    assert d("15 8 * * 1,3,5") == "Mon, Wed, Fri at 8:15 am"
    assert d("0 9 1 * *") == "monthly on the 1st at 9:00 am"
    assert d("0 9 22 * *") == "monthly on the 22nd at 9:00 am"
    assert d("0 */4 * * *") == "every 4 hours"
    assert d("*/20 * * * *") == "every 20 minutes"
    assert d("5 4 * 2 *") == "5 4 * 2 *"                      # unknown shape -> raw


def _fake_create(monkeypatch, created):
    """Stand in for the scheduler-registering creator: persist through the
    plain cron.jobs API so resolve_job_ref/update_job/remove_job all work."""
    import cron.jobs as cron_jobs
    bp = automation._bp()

    def fake(spec, *, origin=None, name=None):
        kwargs = bp.blueprint_to_job_spec(spec, name=name)
        job = cron_jobs.create_job(**kwargs)
        created.append(job)
        return job
    monkeypatch.setattr(bp, "create_blueprint_job", fake)


def test_schedule_applies_edits_and_marks_suggestion(home, monkeypatch):
    from cron import suggestions as cs
    from cron import jobs as cron_jobs
    created = []
    _fake_create(monkeypatch, created)
    # a pending suggestion, as the seed registers it
    sug = cs.add_suggestion(title="Schedule 'out-the-door-brief'", description="d",
                            source="blueprint", job_spec={},
                            dedup_key="blueprint:out-the-door-brief:45 6 * * 1-5")
    assert sug and sug["status"] == "pending"

    r = automation.schedule_blueprint(
        "out-the-door-brief", schedule="30 7 * * 1,2,3,4,5", deliver="local",
        prompt="Brief me, and mention the kids' school run.",
        config={"out_the_door.city": "Boulder, CO", "out_the_door.travel_minutes": "40",
                "not.a.key": "ignored"})
    assert r.get("ok"), r
    job = cron_jobs.resolve_job_ref("blueprint:out-the-door-brief")
    assert job and job["id"] == r["job"]["id"]
    assert job["skills"] == ["out-the-door-brief"]
    assert job["prompt"].startswith("Brief me, and mention")
    assert job["deliver"] == "local"
    assert "30 7" in json.dumps(job["schedule"])
    assert sorted(r["configWritten"]) == ["out_the_door.city", "out_the_door.travel_minutes"]
    assert automation._config_current("out_the_door.city") == "Boulder, CO"
    assert automation._config_current("out_the_door.travel_minutes") == "40"
    assert cs.get_suggestion(sug["id"])["status"] == "accepted"
    entry = r["entry"]
    assert entry["status"] == "scheduled" and entry["job"]["deliver"] == "local"
    assert entry["job"]["scheduleHuman"] == "weekdays at 7:30 am"

    # second submit updates in place — one job, edits applied
    r2 = automation.schedule_blueprint("out-the-door-brief", schedule="0 6 * * *",
                                       deliver="origin", prompt="Shorter brief.")
    assert r2["ok"] and r2["job"]["id"] == job["id"]
    again = cron_jobs.resolve_job_ref("blueprint:out-the-door-brief")
    assert again["prompt"] == "Shorter brief." and again["deliver"] == "origin"
    assert len([j for j in cron_jobs.list_jobs() if j["name"] == "blueprint:out-the-door-brief"]) == 1
    assert len(created) == 1

    # unschedule removes the job and re-offers the suggestion
    r3 = automation.unschedule_blueprint("out-the-door-brief")
    assert r3["ok"] and cron_jobs.resolve_job_ref("blueprint:out-the-door-brief") is None
    assert cs.get_suggestion(sug["id"])["status"] == "pending"
    assert r3["entry"]["status"] == "suggested"


def test_schedule_validation(home, monkeypatch):
    _fake_create(monkeypatch, [])
    with pytest.raises(ValueError):
        automation.schedule_blueprint("money-watch", schedule="not a cron")
    assert "delivery" in automation.schedule_blueprint("money-watch", deliver="carrier-pigeon")["error"]
    assert "empty" in automation.schedule_blueprint("money-watch", prompt="   ")["error"]
    assert "no installed" in automation.schedule_blueprint("nope")["error"]
    assert "not scheduled" in automation.unschedule_blueprint("money-watch")["error"]
    # defaults straight from the SKILL.md when the form sends nothing
    r = automation.schedule_blueprint("money-watch")
    assert r["ok"] and r["entry"]["job"]["scheduleHuman"] == "every 4 hours"
    assert r["entry"]["job"]["prompt"] == "Watch prices."


def test_config_fields_carry_file_kind_and_templates(home):
    _skill(home, "money-watch-x", schedule="0 */4 * * *", prompt="w", level=3,
           config=[{"key": "money_watch.watchlist_path", "default": "~/life/watchlist.md",
                    "prompt": "Watchlist file"}])
    e = [x for x in automation.list_blueprints()["entries"] if x["name"] == "money-watch-x"][0]
    f = e["config"][0]
    assert f["kind"] == "file" and f["files"][0]["name"] == ""
    assert f["files"][0]["template"].startswith("type | label | url | threshold | notes")
    assert "price | stock | protect" in f["hint"]
    # every declared input-file key of the collection is either a file or a folder
    for key, meta in automation.INPUT_FILES.items():
        assert meta["kind"] in ("file", "dir"), key
        for spec in meta["files"]:
            assert isinstance(spec["template"], str) and spec["template"].strip(), (key, spec)


def test_input_files_round_trip_confined_to_home(home, monkeypatch, tmp_path):
    fake_home = tmp_path / "home"; fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))
    # missing file: reads as empty, non-existent
    r = automation.read_input("~/life/watchlist.md")
    assert r["kind"] == "file" and r["exists"] is False and r["content"] == ""
    assert r["display"] == "~/life/watchlist.md"
    # write creates parents and persists
    w = automation.write_input("~/life/watchlist.md", "type | label\nprice | Desk\n")
    assert w["ok"] and (fake_home / "life" / "watchlist.md").read_text() == "type | label\nprice | Desk\n"
    r2 = automation.read_input("~/life/watchlist.md")
    assert r2["exists"] and r2["content"].startswith("type | label")
    # folders list their files (relative names, nested one or two levels)
    automation.write_input("~/life/people/sam.md", "---\nname: Sam\n---\n")
    d = automation.read_input("~/life")
    assert d["kind"] == "dir" and {f["name"] for f in d["files"]} == {"watchlist.md", "people/sam.md"}
    # confinement
    with pytest.raises(ValueError):
        automation.read_input("/etc/passwd")
    with pytest.raises(ValueError):
        automation.read_input("~/../../etc/passwd")
    with pytest.raises(ValueError):
        automation.write_input("~/.hermes/config.yaml", "x")
    with pytest.raises(ValueError):
        automation.read_input("~/.ssh/id_ed25519")
    with pytest.raises(ValueError):
        automation.write_input("~/life", "x")          # a folder, not a file
    with pytest.raises(ValueError):
        automation.write_input("~/life/big.md", "x" * (automation.MAX_FILE_BYTES + 1))
