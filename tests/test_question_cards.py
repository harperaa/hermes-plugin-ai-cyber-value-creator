"""Question-card backend units: marker parsing, exact session lookup."""
import json
import os
import sqlite3
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _load_progress(monkeypatch, tmp_path):
    import importlib.util
    root = Path(__file__).resolve().parent.parent
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    pkg = "acvc_qtest"
    spec = importlib.util.spec_from_file_location(
        pkg, root / "__init__.py", submodule_search_locations=[str(root)])
    m = importlib.util.module_from_spec(spec)
    sys.modules[pkg] = m
    spec.loader.exec_module(m)
    import importlib
    return importlib.import_module(f"{pkg}.progress")


def test_find_worker_session_exact_match(monkeypatch, tmp_path):
    progress = _load_progress(monkeypatch, tmp_path)
    db = tmp_path / "state.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY, session_id TEXT, role TEXT, content TEXT)")
    rows = [
        ("s_other", "user", "work kanban task t_bbb"),
        ("s_mentions", "assistant", "board shows t_aaa and t_bbb"),  # LIKE-trap
        ("s_right_old", "user", "work kanban task t_aaa"),
        ("s_right_new", "user", "work kanban task t_aaa"),  # respawn: newest wins
    ]
    for sid, role, content in rows:
        conn.execute("INSERT INTO messages (session_id, role, content) VALUES (?,?,?)", (sid, role, content))
    conn.commit(); conn.close()
    assert progress._find_worker_session("t_aaa") == "s_right_new"
    assert progress._find_worker_session("t_bbb") == "s_other"
    assert progress._find_worker_session("t_zzz") is None


def test_question_marker_constant(monkeypatch, tmp_path):
    progress = _load_progress(monkeypatch, tmp_path)
    assert progress.QUESTION_MARKER == "### ❓ QUESTION FOR YOU"
