import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from app.core.db import Base


class DataModel(Base):
    """A saved data download: which dataset, columns and filters to export.

    It stores the query, not the data, so every download returns the latest
    data of the studies the viewer may see."""

    __tablename__ = "data_model"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True,
        server_default=text("gen_random_uuid()")
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
    )
    owner: Mapped["User"] = relationship(lazy="selectin", foreign_keys=[owner_id])
    name: Mapped[str]
    description: Mapped[Optional[str]]
    # A DataModelDefinition (app/schemas/data_model.py).
    definition: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # Public models are listed for everyone, signed in or not.
    is_public: Mapped[bool] = mapped_column(
        nullable=False, server_default=text("false"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("now()")
    )


from app.models.user import User
