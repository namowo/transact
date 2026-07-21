from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import text

from app.core.db import Base


class WebAuthnCredential(Base):
    """A passkey registered by a user for WebAuthn login."""

    __tablename__ = "webauthn_credential"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    credential_id: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    public_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    sign_count: Mapped[int] = mapped_column(nullable=False, server_default=text("0"))
    device_name: Mapped[Optional[str]]
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("now()")
    )
    last_used_at: Mapped[Optional[datetime]]
