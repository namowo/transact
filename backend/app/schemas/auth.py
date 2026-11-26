from typing import List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class EmailVerificationConfirm(BaseModel):
    token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class InvitationAccept(BaseModel):
    token: str
    password: str = Field(min_length=8)


class AuthConfig(BaseModel):
    """The instance's sign-up and sign-in policy (from the environment)."""

    registration_enabled: bool
    invitations_enabled: bool
    two_factor_required: bool


class TwoFactorChallenge(BaseModel):
    """The password was right; a second factor is needed to sign in.

    With "totp" in `methods`, send a code with `login_token` to
    /auth/login/two-factor. With "passkey", the user may sign in with a
    passkey instead."""

    two_factor_required: Literal[True] = True
    login_token: Optional[str] = None
    methods: List[Literal["totp", "passkey"]]


class TwoFactorLogin(BaseModel):
    login_token: str
    # From the authenticator app, or a recovery code.
    code: str = Field(min_length=1, max_length=32)


class TotpSetup(BaseModel):
    secret: str
    # otpauth:// link, shown as a QR code.
    provisioning_uri: str


class TotpCode(BaseModel):
    code: str = Field(min_length=1, max_length=32)


class TotpDisable(BaseModel):
    current_password: str
    code: str = Field(min_length=1, max_length=32)


class RecoveryCodes(BaseModel):
    # Shown once; only their hashes are stored.
    recovery_codes: List[str]
