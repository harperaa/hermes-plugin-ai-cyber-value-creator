"""Provider-level tests against the real hermes DashboardAuthProvider ABC."""
import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mentor_auth  # noqa: E402


def _provider(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    monkeypatch.setenv("HERMES_DASHBOARD_BASIC_AUTH_SECRET", "x" * 32)
    importlib.reload(mentor_auth)
    return mentor_auth.build_provider()


def test_claim_then_login(tmp_path, monkeypatch):
    from hermes_cli.dashboard_auth import InvalidCredentialsError
    p = _provider(tmp_path, monkeypatch)
    assert "New Login" in p.display_name
    # weak password rejected, store not created
    with pytest.raises(InvalidCredentialsError):
        p.complete_password_login(username="a@b.co", password="weakpass")
    assert mentor_auth.load_store() is None
    # non-email username rejected
    with pytest.raises(InvalidCredentialsError):
        p.complete_password_login(username="admin", password="Str0ng!pw")
    # claim
    s = p.complete_password_login(username="a@b.co", password="Str0ng!pw")
    assert s.email == "a@b.co" and s.provider == "mentor"
    assert p.display_name == "Email & Password"
    # session verify roundtrip
    assert p.verify_session(access_token=s.access_token).user_id == "a@b.co"
    # normal login now; wrong password rejected
    p.complete_password_login(username="A@B.CO", password="Str0ng!pw")
    with pytest.raises(InvalidCredentialsError):
        p.complete_password_login(username="a@b.co", password="Wr0ng!pw")


def test_register_skips_when_basic_env_set(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    monkeypatch.setenv("HERMES_DASHBOARD_BASIC_AUTH_PASSWORD", "Env!Passw0rd")
    importlib.reload(mentor_auth)

    class Ctx:
        called = False
        def register_dashboard_auth_provider(self, provider):
            Ctx.called = True

    mentor_auth.register_mentor_auth(Ctx())
    assert Ctx.called is False


def test_register_registers_when_env_clear(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    monkeypatch.delenv("HERMES_DASHBOARD_BASIC_AUTH_PASSWORD", raising=False)
    monkeypatch.delenv("HERMES_DASHBOARD_BASIC_AUTH_PASSWORD_HASH", raising=False)
    importlib.reload(mentor_auth)

    seen = {}
    class Ctx:
        def register_dashboard_auth_provider(self, provider):
            seen["name"] = provider.name
    mentor_auth.register_mentor_auth(Ctx())
    assert seen.get("name") == "mentor"


def test_adoption_resets_claimed_password(tmp_path, monkeypatch):
    from hermes_cli.dashboard_auth import InvalidCredentialsError
    p = _provider(tmp_path, monkeypatch)
    p.complete_password_login(username="own@er.io", password="Cl@im3dpw")
    mentor_auth.adopt_env_password("R3set!fromenv", "")
    p2 = mentor_auth.build_provider()
    with pytest.raises(InvalidCredentialsError):
        p2.complete_password_login(username="own@er.io", password="Cl@im3dpw")
    s = p2.complete_password_login(username="own@er.io", password="R3set!fromenv")
    assert s.email == "own@er.io"
