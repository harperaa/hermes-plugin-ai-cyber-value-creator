"""mentor-auth unit tests — hermetic (tmp HERMES_HOME, no hermes dashboard)."""
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mentor_auth  # noqa: E402


def _fresh(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    importlib.reload(mentor_auth)
    return mentor_auth


def test_policy():
    assert mentor_auth.password_meets_policy("Str0ng!pass")
    assert not mentor_auth.password_meets_policy("short1!A"[:7])
    assert not mentor_auth.password_meets_policy("alllowercase1!")
    assert not mentor_auth.password_meets_policy("ALLUPPERCASE1!")
    assert not mentor_auth.password_meets_policy("NoSpecials11")
    assert mentor_auth.looks_like_email("a@b.co")
    assert not mentor_auth.looks_like_email("admin")


def test_hash_roundtrip(tmp_path, monkeypatch):
    m = _fresh(tmp_path, monkeypatch)
    h = m.hash_password("Sup3r!secret")
    assert h.startswith("scrypt$")
    assert m._verify_password("Sup3r!secret", h)
    assert not m._verify_password("wrong", h)


def test_adopt_creates_and_overwrites(tmp_path, monkeypatch):
    m = _fresh(tmp_path, monkeypatch)
    assert m.load_store() is None
    login = m.adopt_env_password("Adopt3d!pw", "")
    assert login == "admin"
    s1 = m.load_store()
    assert s1["source"] == "env"
    assert m._verify_password("Adopt3d!pw", s1["password_hash"])
    # overwrite keeps stored email when username not supplied
    m.adopt_env_password("N3w!password", "")
    s2 = m.load_store()
    assert s2["email"] == "admin"
    assert m._verify_password("N3w!password", s2["password_hash"])
    assert not m._verify_password("Adopt3d!pw", s2["password_hash"])
    # explicit username wins
    m.adopt_env_password("N3w!password2", "coach@example.com")
    assert m.load_store()["email"] == "coach@example.com"


def test_store_write_permissions(tmp_path, monkeypatch):
    m = _fresh(tmp_path, monkeypatch)
    m.adopt_env_password("Adopt3d!pw", "x@y.io")
    mode = m.store_path().stat().st_mode & 0o777
    assert mode == 0o600
