import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from app.core.db import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True, server_default=text("gen_random_uuid()")
    )
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    hashed_password: Mapped[str]
    first_name: Mapped[str]
    last_name: Mapped[str]
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"))
    is_verified: Mapped[bool] = mapped_column(
        nullable=False, server_default=text("false")
    )
    passkey_prompt_dismissed: Mapped[bool] = mapped_column(
        nullable=False, server_default=text("false")
    )

    # Interactive guides (e.g. "onboarding", "new-study") the user has
    # finished or skipped, so they aren't started automatically again.
    completed_tours: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )

    # BCP 47 language tag (e.g. "en-US", "de-DE"); decides how numbers are
    # typed and shown, e.g. the decimal separator.
    locale: Mapped[str] = mapped_column(
        nullable=False, server_default=text("'en-US'")
    )

    # The user's saved column sort per data table ({"samples": [{"field",
    # "order"}, ...]}); CSV exports follow it too. Missing tables use the app
    # default.
    table_sorts: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    laboratory_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("laboratory.id", ondelete="RESTRICT")
    )
    laboratory: Mapped[Optional["Laboratory"]] = relationship(
        lazy="selectin", foreign_keys=[laboratory_id]
    )

    groups: Mapped[list["UserGroup"]] = relationship(
        secondary="user_group_member", lazy="selectin", order_by="UserGroup.name"
    )

    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("now()")
    )

    # --- Permissions --------------------------------------------------------

    @property
    def permissions(self) -> frozenset[str]:
        """Everything the user's groups grant (see app.core.permission_catalog).

        Laboratory-scoped permissions only apply to the user's own
        laboratory; use `can_in_laboratory` for those."""
        return frozenset(
            permission for group in self.groups for permission in group.permissions
        )

    def can(self, permission: "Permission") -> bool:
        return permission.value in self.permissions

    def can_in_laboratory(
        self, permission: "Permission", laboratory_id: Optional[uuid.UUID]
    ) -> bool:
        return (
            laboratory_id is not None
            and self.laboratory_id == laboratory_id
            and self.can(permission)
        )


from app.core.permission_catalog import Permission  # noqa: E402
from app.models.laboratory import Laboratory  # noqa: E402
from app.models.user_group import UserGroup  # noqa: E402
