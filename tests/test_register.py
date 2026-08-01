

def test_indexed_skill_sync(tmp_path, monkeypatch):
    import importlib, sys
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    monkeypatch.setitem(sys.modules, "hermes_constants", None)  # force env fallback
    import __init__ as plug  # noqa: F401
    mod = importlib.import_module("__init__") if "__init__" in sys.modules else plug
    mod._sync_indexed_skills()
    dst = tmp_path / "skills" / "marketing-pro-router" / "SKILL.md"
    assert dst.exists()
    assert "digital-marketing-pro" in dst.read_text()
    # idempotent: second sync leaves content identical
    before = dst.read_text()
    mod._sync_indexed_skills()
    assert dst.read_text() == before
