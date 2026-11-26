import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

ALGORITHM = "HS256"

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(
    subject: str, expires_delta: timedelta | None = None, *, mfa: bool = False
) -> str:
    """A session token. `mfa` says the sign-in used a second factor (a
    one-time code, or a passkey with user verification)."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(seconds=settings.VITE_JWT_LIFETIME_SECONDS)
    )
    to_encode = {"sub": subject, "exp": expire, "mfa": mfa}
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    # Tokens with an audience (e.g. the two-factor login token) are rejected
    # here: PyJWT refuses an `aud` claim when no audience is expected.
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])


TWO_FACTOR_LOGIN_AUDIENCE = "two-factor-login"


def create_two_factor_login_token(subject: str) -> str:
    """Proof that the password was right, exchanged for a session once the
    one-time code is too. Not a session token itself."""
    expire = datetime.now(timezone.utc) + timedelta(
        seconds=settings.TWO_FACTOR_LOGIN_TTL_SECONDS
    )
    to_encode = {"sub": subject, "exp": expire, "aud": TWO_FACTOR_LOGIN_AUDIENCE}
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)


def decode_two_factor_login_token(token: str) -> str | None:
    """The user id of a valid two-factor login token, else None."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=TWO_FACTOR_LOGIN_AUDIENCE,
        )
    except jwt.PyJWTError:
        return None
    return payload.get("sub")


def generate_token() -> str:
    """Generate a random, URL-safe raw token (for email verify / password reset)."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash a raw token for storage - only the hash is persisted to the DB."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
