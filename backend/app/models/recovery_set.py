from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class RecoverySet(Base):
    """Groups recoveries that share the same attributes, to make data entry easier."""

    __tablename__ = "recovery_set"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    name: Mapped[Optional[str]]
    recoveries: Mapped[list["Recovery"]] = relationship(
        lazy="selectin",
        back_populates="recovery_set",
        foreign_keys="Recovery.recovery_set_id",
    )


from app.models.recovery import Recovery
