import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import text

from app.core.db import Base


class ApiKey(Base):
    """A personal API key a user can use to authenticate against the API."""

    __tablename__ = "api_key"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True,
        server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[Optional[str]]
    key_hash: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    prefix: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("now()")
    )
    last_used_at: Mapped[Optional[datetime]]
    expires_at: Mapped[Optional[datetime]]
