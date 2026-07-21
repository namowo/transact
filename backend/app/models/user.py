from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from app.core.db import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    hashed_password: Mapped[str]
    first_name: Mapped[str]
    last_name: Mapped[str]
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"))
    is_verified: Mapped[bool] = mapped_column(
        nullable=False, server_default=text("false")
    )
    is_superuser: Mapped[bool] = mapped_column(
        nullable=False, server_default=text("false")
    )
    can_quality_check: Mapped[bool] = mapped_column(
        nullable=False, server_default=text("false")
    )
    can_manage_lab_users: Mapped[bool] = mapped_column(
        nullable=False, server_default=text("false")
    )
    passkey_prompt_dismissed: Mapped[bool] = mapped_column(
        nullable=False, server_default=text("false")
    )

    laboratory_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("laboratory.id", ondelete="RESTRICT")
    )
    laboratory: Mapped[Optional["Laboratory"]] = relationship(
        lazy="selectin", foreign_keys=[laboratory_id]
    )

    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("now()")
    )


from app.models.laboratory import Laboratory
