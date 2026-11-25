import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from app.core.db import Base

# Which users belong to which groups.
user_group_member = Table(
    "user_group_member",
    Base.metadata,
    Column(
        "user_id",
        PGUUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "group_id",
        PGUUID(as_uuid=True),
        ForeignKey("user_group.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)


class UserGroup(Base):
    """A named set of permissions (see app.core.permission_catalog).

    A group without a laboratory is global: admins define it and it can be
    given to anyone. A group with a laboratory belongs to that laboratory:
    its lab admins define it, it may only hold laboratory permissions, and
    only the laboratory's members can be in it.
    """

    __tablename__ = "user_group"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        index=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str]
    description: Mapped[Optional[str]]
    # Set for the built-in groups (see SystemGroup); they can't be deleted.
    system_key: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    laboratory_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("laboratory.id", ondelete="CASCADE"),
        index=True,
    )
    permissions: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("now()")
    )

    laboratory: Mapped[Optional["Laboratory"]] = relationship(lazy="selectin")


from app.models.laboratory import Laboratory  # noqa: E402
