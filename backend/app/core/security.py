from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any


ALLOWED_ROLES = {"admin", "mentor", "client"}
PBKDF2_ITERATIONS = 120_000


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = hashed_password.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        expected = bytes.fromhex(digest_hex)
        salt = bytes.fromhex(salt_hex)
        current = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations),
        )
        return hmac.compare_digest(current, expected)
    except Exception:
        return False


def create_access_token(user_id: str, role: str, secret: str, ttl_seconds: int = 3600) -> str:
    if role not in ALLOWED_ROLES:
        raise ValueError("invalid role")

    payload = {
        "sub": user_id,
        "role": role,
        "exp": int(time.time()) + ttl_seconds,
    }
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(secret.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"


def verify_access_token(token: str, secret: str) -> dict[str, Any] | None:
    try:
        payload_b64, signature = token.split(".", 1)
        expected_signature = hmac.new(
            secret.encode("utf-8"),
            payload_b64.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            return None

        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
        if payload.get("role") not in ALLOWED_ROLES:
            return None
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        if not payload.get("sub"):
            return None
        return payload
    except Exception:
        return None
