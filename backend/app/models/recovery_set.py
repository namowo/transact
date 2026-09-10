import uuid
from typing import Optional

from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.sql import text

from app.core.db import Base


class RecoverySet(Base):
    """Groups recoveries that share the same attributes, to make data entry easier."""

    __tablename__ = "recovery_set"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True,
        server_default=text("gen_random_uuid()")
    )
    name: Mapped[Optional[str]]
    recoveries: Mapped[list["Recovery"]] = relationship(
        lazy="selectin",
        back_populates="recovery_set",
        foreign_keys="Recovery.recovery_set_id",
    )


from app.models.recovery import Recovery
