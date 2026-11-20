"""Simple, zero-dependency password hashing and session token helpers."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

PBKDF2_ITERATIONS = 120_000
SESSION_TTL_DAYS = 30
SESSION_COOKIE_NAME = "openupsc_session"


def hash_password(password: str) -> str:
    """Hash a plaintext password using PBKDF2-HMAC-SHA256 with a random salt."""
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string.")
    salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${derived.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a plaintext password against a stored PBKDF2 hash in constant time."""
    if not isinstance(password, str) or not isinstance(stored_hash, str):
        return False
    try:
        scheme, iterations_str, salt, expected_hex = stored_hash.split("$", 3)
        iterations = int(iterations_str)
        if scheme != "pbkdf2_sha256" or iterations <= 0 or not salt or not expected_hex:
            return False
        derived = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        )
        return hmac.compare_digest(derived.hex(), expected_hex)
    except (ValueError, TypeError, AttributeError):
        return False


def generate_session_token() -> tuple[str, str]:
    """Return a secure random session token and its ISO UTC expiry timestamp."""
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=SESSION_TTL_DAYS)).isoformat()
    return token, expires_at
