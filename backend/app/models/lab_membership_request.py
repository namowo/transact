import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from app.core.db import Base


class LabMembershipRequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    denied = "denied"


class LabMembershipRequest(Base):
    __tablename__ = "lab_membership_request"
    __table_args__ = (
        Index(
            "ix_lab_membership_request_one_pending_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    user: Mapped["User"] = relationship(lazy="selectin", foreign_keys=[user_id])

    laboratory_id: Mapped[int] = mapped_column(
        ForeignKey("laboratory.id", ondelete="CASCADE"), nullable=False
    )
    laboratory: Mapped["Laboratory"] = relationship(
        lazy="selectin", foreign_keys=[laboratory_id]
    )

    status: Mapped[LabMembershipRequestStatus] = mapped_column(
        SAEnum(
            LabMembershipRequestStatus,
            name="lab_membership_request_status",
            native_enum=False,
            length=20,
        ),
        nullable=False,
        server_default=text("'pending'"),
    )

    reviewed_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL")
    )
    reviewed_by: Mapped[Optional["User"]] = relationship(
        lazy="selectin", foreign_keys=[reviewed_by_id]
    )
    reviewed_at: Mapped[Optional[datetime]]

    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("now()")
    )


from app.models.laboratory import Laboratory
from app.models.user import User
