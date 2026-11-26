"""Time-based one-time passwords (RFC 6238) for authenticator apps, and the
recovery codes that stand in for them when the device is lost."""

import base64
import hashlib
import hmac
import secrets
import struct
import time
from typing import Optional
from urllib.parse import quote, urlencode

DIGITS = 6
PERIOD_SECONDS = 30
# Accept the previous and the next code too, for clock drift.
WINDOW = 1

RECOVERY_CODE_COUNT = 10


def generate_secret() -> str:
    """A random 160-bit secret, base32 as authenticator apps expect."""
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def _decode_secret(secret: str) -> bytes:
    padded = secret.upper() + "=" * (-len(secret) % 8)
    return base64.b32decode(padded)


def code_at(secret: str, step: int) -> str:
    """The code for time step `step` (RFC 4226 HOTP with SHA-1)."""
    digest = hmac.new(_decode_secret(secret), struct.pack(">Q", step), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(value % 10**DIGITS).zfill(DIGITS)


def current_step(now: Optional[float] = None) -> int:
    return int((time.time() if now is None else now) // PERIOD_SECONDS)


def verify(
    secret: str,
    code: str,
    *,
    last_used_step: Optional[int] = None,
    now: Optional[float] = None,
) -> Optional[int]:
    """The time step `code` belongs to, or None if it's wrong.

    Steps up to `last_used_step` are refused, so a code can't be used twice."""
    code = normalize_code(code)
    if len(code) != DIGITS or not code.isdigit():
        return None
    step = current_step(now)
    for candidate in range(step - WINDOW, step + WINDOW + 1):
        if last_used_step is not None and candidate <= last_used_step:
            continue
        if hmac.compare_digest(code_at(secret, candidate), code):
            return candidate
    return None


def provisioning_uri(secret: str, account: str, issuer: str) -> str:
    """The otpauth:// link authenticator apps read from the QR code."""
    label = quote(f"{issuer}:{account}")
    params = urlencode(
        {
            "secret": secret,
            "issuer": issuer,
            "algorithm": "SHA1",
            "digits": DIGITS,
            "period": PERIOD_SECONDS,
        }
    )
    return f"otpauth://totp/{label}?{params}"


def normalize_code(code: str) -> str:
    return "".join(code.split()).replace("-", "").lower()


def generate_recovery_codes() -> list[str]:
    """Single-use codes like "3f9a1-c07be", shown to the user once."""
    codes = []
    for _ in range(RECOVERY_CODE_COUNT):
        raw = secrets.token_hex(5)
        codes.append(f"{raw[:5]}-{raw[5:]}")
    return codes


def hash_recovery_code(code: str) -> str:
    return hashlib.sha256(normalize_code(code).encode("utf-8")).hexdigest()
