"""mentor-auth — first-visit "claim" dashboard login (email + password).

Paperclip-style onboarding for hosted deployments: when no credential store
exists yet, the FIRST login attempt creates the account — the visitor enters
their email address and a password, the credential persists to the volume,
and every later visit is a normal login. No email sending, no reset flow.

Recovery / reset is environment-driven (wired by the distribution image's
seed hook, which owns deployment behavior): setting
``HERMES_DASHBOARD_BASIC_AUTH_PASSWORD`` in the hosting console makes the
next boot ADOPT that value into the store via :func:`adopt_env_password`
(and the seed hook then blanks the env var so hermes' bundled ``basic``
provider never co-registers). Removing the variable afterward keeps the
adopted credential.

Trust model (accepted, mirrors paperclip's claim flow): the first visitor
to an unclaimed instance owns it. Hosted deploys are only unclaimed for the
minutes between deploy and the owner's first login; the operator can always
take over by setting the env password (adoption overwrites the store) or by
deleting ``$HERMES_HOME/mentor-auth.json`` from a shell.

Crypto matches hermes' bundled ``basic`` provider exactly (stdlib scrypt
password hashes in the ``scrypt$n$r$p$salt$dk`` format, stateless
HMAC-SHA256-signed session tokens). The code is deliberately self-contained
rather than importing from ``plugins.dashboard_auth.basic`` so this plugin
never depends on the host's bundled-plugin import layout.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Password policy (single source of truth — the distribution seed hook's
# boot-time gate mirrors these rules; keep them in sync).
# ---------------------------------------------------------------------------

PASSWORD_RULES = (
    "at least 8 characters with 1 UPPERCASE letter, 1 lowercase letter, "
    "and 1 special character (e.g. ! @ # $ %)"
)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def password_meets_policy(password: str) -> bool:
    return (
        len(password) >= 8
        and re.search(r"[A-Z]", password) is not None
        and re.search(r"[a-z]", password) is not None
        and re.search(r"[^A-Za-z0-9]", password) is not None
    )


def looks_like_email(value: str) -> bool:
    return bool(_EMAIL_RE.match(value.strip()))


# ---------------------------------------------------------------------------
# scrypt hashing + HMAC token signing (format-identical to the basic provider)
# ---------------------------------------------------------------------------

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_DKLEN = 32
_SCRYPT_SALT_BYTES = 16
_SIG_LEN = hashlib.sha256().digest_size

_DEFAULT_TTL_SECONDS = 12 * 60 * 60
_REFRESH_TTL_SECONDS = 30 * 24 * 60 * 60


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SCRYPT_SALT_BYTES)
    dk = hashlib.scrypt(
        password.encode("utf-8"), salt=salt,
        n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P,
        dklen=_SCRYPT_DKLEN, maxmem=0,
    )
    return (
        f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}$"
        f"{base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"
    )


def _verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, n_s, r_s, p_s, salt_b64, dk_b64 = encoded.split("$")
        if scheme != "scrypt":
            return False
        n, r, p = int(n_s), int(r_s), int(p_s)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(dk_b64)
    except (ValueError, TypeError):
        return False
    try:
        actual = hashlib.scrypt(
            password.encode("utf-8"), salt=salt,
            n=n, r=r, p=p, dklen=len(expected), maxmem=0,
        )
    except (ValueError, MemoryError):
        return False
    return hmac.compare_digest(actual, expected)


_DUMMY_HASH = hash_password("dummy-password-for-constant-time-verify")


def _sign(payload: dict, secret: bytes) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode()
    sig = hmac.new(secret, raw, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(raw + sig).decode()


def _unsign(token: str, secret: bytes) -> Optional[dict]:
    try:
        blob = base64.urlsafe_b64decode(token.encode())
        if len(blob) <= _SIG_LEN:
            return None
        raw, sig = blob[:-_SIG_LEN], blob[-_SIG_LEN:]
        expected = hmac.new(secret, raw, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            return None
        return json.loads(raw)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Credential store — one JSON file on the data volume
# ---------------------------------------------------------------------------


def store_path() -> Path:
    home = os.environ.get("HERMES_HOME", "").strip()
    root = Path(home) if home else Path.home() / ".hermes"
    return root / "mentor-auth.json"


def load_store() -> Optional[dict]:
    try:
        data = json.loads(store_path().read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("email") and data.get("password_hash"):
            return data
    except FileNotFoundError:
        return None
    except Exception:
        logger.warning("mentor-auth: unreadable store at %s", store_path(),
                       exc_info=True)
    return None


def _write_store(data: dict, *, exclusive: bool) -> bool:
    """Atomic 0600 write. With ``exclusive``, lose gracefully if a
    concurrent claim already created the store (first writer wins)."""
    path = store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        if exclusive:
            try:
                os.link(tmp, path)  # atomic create-if-absent
            except FileExistsError:
                return False
            finally:
                os.unlink(tmp)
        else:
            os.replace(tmp, path)
        os.chmod(path, 0o600)
        return True
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def adopt_env_password(password: str, username: str = "") -> str:
    """Overwrite the stored credential from an operator-supplied password.

    Called by the distribution image's boot seed whenever the operator sets
    ``HERMES_DASHBOARD_BASIC_AUTH_PASSWORD`` — this IS the reset flow. The
    login name becomes ``username`` when given, else the previously stored
    email, else ``admin``. Returns the login name adopted.
    """
    if not password:
        raise ValueError("adopt_env_password: empty password")
    existing = load_store() or {}
    login = (username or "").strip() or existing.get("email") or "admin"
    _write_store(
        {
            "email": login,
            "password_hash": hash_password(password),
            "created_at": existing.get("created_at") or int(time.time()),
            "adopted_at": int(time.time()),
            "source": "env",
        },
        exclusive=False,
    )
    logger.info("mentor-auth: credential reset from environment (login=%s)", login)
    return login


# ---------------------------------------------------------------------------
# Provider (registered via ctx.register_dashboard_auth_provider)
# ---------------------------------------------------------------------------

# Rendered by the login page as "Sign in with <label>" in a compressed
# uppercase display font — keep these SHORT or they become unreadable.
# The full password rules live in the install guide and the claim-failure
# path; the label carries only a compact hint.
_CLAIM_LABEL = "Your New Login (8+ Chars, Mixed Case + Symbol)"
_NORMAL_LABEL = "Email & Password"


def _resolve_secret() -> bytes:
    raw = os.environ.get("HERMES_DASHBOARD_BASIC_AUTH_SECRET", "").strip()
    if not raw:
        try:
            from hermes_cli.config import cfg_get, load_config
            raw = str(
                cfg_get(load_config(), "dashboard", "basic_auth", default={})
                .get("secret", "") or ""
            ).strip()
        except Exception:
            raw = ""
    if not raw:
        logger.info(
            "mentor-auth: no signing secret configured; using a random "
            "per-process key (sessions won't survive a restart). Set "
            "HERMES_DASHBOARD_BASIC_AUTH_SECRET for stable sessions."
        )
        return secrets.token_bytes(32)
    for decoder in (base64.b64decode, bytes.fromhex):
        try:
            decoded = decoder(raw)
            if len(decoded) >= 16:
                return decoded
        except (ValueError, TypeError):
            pass
    return raw.encode("utf-8")


def build_provider():
    """Construct the provider. Imports hermes lazily so this module stays
    importable (for adopt_env_password / tests) outside a hermes process."""
    from hermes_cli.dashboard_auth import (
        DashboardAuthProvider,
        InvalidCredentialsError,
        LoginStart,
        RefreshExpiredError,
        Session,
    )

    class MentorAuthProvider(DashboardAuthProvider):
        name = "mentor"
        display_name = _NORMAL_LABEL if load_store() else _CLAIM_LABEL
        supports_password = True

        def __init__(self) -> None:
            self._secret = _resolve_secret()
            self._ttl = _DEFAULT_TTL_SECONDS

        # -- OAuth surface: unused ------------------------------------------
        def start_login(self, *, redirect_uri: str) -> LoginStart:
            raise NotImplementedError("mentor-auth is password-only")

        def complete_login(self, *, code: str, state: str,
                           code_verifier: str, redirect_uri: str) -> Session:
            raise NotImplementedError("mentor-auth is password-only")

        # -- password login: claim-or-verify --------------------------------
        def complete_password_login(self, *, username: str,
                                    password: str) -> Session:
            store = load_store()
            if store is None:
                return self._claim(username, password)
            email_ok = hmac.compare_digest(
                username.strip().lower().encode("utf-8"),
                str(store["email"]).strip().lower().encode("utf-8"),
            )
            target = store["password_hash"] if email_ok else _DUMMY_HASH
            if not (_verify_password(password, target) and email_ok):
                raise InvalidCredentialsError("invalid username or password")
            return self._mint(str(store["email"]))

        def _claim(self, username: str, password: str) -> Session:
            email = username.strip()
            if not looks_like_email(email):
                raise InvalidCredentialsError(
                    "claim rejected: username must be an email address"
                )
            if not password_meets_policy(password):
                raise InvalidCredentialsError(
                    f"claim rejected: password must be {PASSWORD_RULES}"
                )
            created = _write_store(
                {
                    "email": email,
                    "password_hash": hash_password(password),
                    "created_at": int(time.time()),
                    "source": "claim",
                },
                exclusive=True,
            )
            if not created:
                # Lost a claim race — fall through to normal verification so
                # the actual winner's credential is authoritative.
                return self.complete_password_login(
                    username=username, password=password
                )
            logger.info("mentor-auth: instance claimed by %s", email)
            self.display_name = _NORMAL_LABEL
            return self._mint(email)

        # -- session lifecycle (stateless HMAC, mirrors basic) ---------------
        def verify_session(self, *, access_token: str) -> Optional[Session]:
            payload = _unsign(access_token, self._secret)
            if (payload is None or payload.get("kind") != "access"
                    or payload.get("exp", 0) <= int(time.time())):
                return None
            return self._session(access_token, "", payload)

        def refresh_session(self, *, refresh_token: str) -> Session:
            if not refresh_token:
                raise RefreshExpiredError("no refresh token present")
            payload = _unsign(refresh_token, self._secret)
            if (payload is None or payload.get("kind") != "refresh"
                    or payload.get("exp", 0) <= int(time.time())):
                raise RefreshExpiredError("refresh token expired or invalid")
            return self._mint(str(payload.get("sub", "")))

        def revoke_session(self, *, refresh_token: str) -> None:
            return None

        # -- internals -------------------------------------------------------
        def _mint(self, email: str) -> Session:
            now = int(time.time())
            exp = now + self._ttl
            return Session(
                user_id=email, email=email, display_name=email, org_id="",
                provider=self.name, expires_at=exp,
                access_token=_sign({"sub": email, "kind": "access",
                                    "exp": exp}, self._secret),
                refresh_token=_sign({"sub": email, "kind": "refresh",
                                     "exp": now + _REFRESH_TTL_SECONDS},
                                    self._secret),
            )

        def _session(self, access_token: str, refresh_token: str,
                     payload: dict) -> Session:
            email = str(payload.get("sub", ""))
            return Session(
                user_id=email, email=email, display_name=email, org_id="",
                provider=self.name, expires_at=int(payload["exp"]),
                access_token=access_token, refresh_token=refresh_token,
            )

    return MentorAuthProvider()


def register_mentor_auth(ctx) -> None:
    """Register the claim provider unless the operator configured hermes'
    bundled ``basic`` provider directly (env password/hash present) — in
    that case defer entirely so users never see two password forms. In the
    distribution image the seed hook adopts-then-blanks those vars before
    services start, so mentor is always the active provider there."""
    if (os.environ.get("HERMES_DASHBOARD_BASIC_AUTH_PASSWORD", "").strip()
            or os.environ.get("HERMES_DASHBOARD_BASIC_AUTH_PASSWORD_HASH",
                              "").strip()):
        logger.debug("mentor-auth: basic env credentials present — deferring")
        return
    try:
        provider = build_provider()
    except ImportError:
        logger.debug("mentor-auth: hermes dashboard_auth unavailable — skipped")
        return
    except Exception:
        logger.warning("mentor-auth: provider construction failed",
                       exc_info=True)
        return
    ctx.register_dashboard_auth_provider(provider)
