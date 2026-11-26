"""Encryption of secrets stored in the database (e.g. authenticator app
secrets), so a copy of the database alone doesn't reveal them."""

from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

import base64

from app.core.config import settings


class DecryptionError(Exception):
    """The value wasn't encrypted with the current key."""


@lru_cache
def _fernet() -> Fernet:
    secret = settings.TWO_FACTOR_ENCRYPTION_KEY or settings.JWT_SECRET_KEY
    # Any string works as the configured key: derive a proper 32-byte key
    # from it. The info string keeps it distinct from other uses of the
    # same secret (e.g. signing session tokens).
    key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"transact:two-factor-secret-encryption",
    ).derive(secret.encode("utf-8"))
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode("utf-8")).decode("ascii")


def decrypt(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError) as e:
        raise DecryptionError() from e
