from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Contact(Base):
    __tablename__ = "contact"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    donor_surface_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("surface.id", ondelete="SET NULL")
    )
    donor_surface: Mapped[Optional["Surface"]] = relationship(
        lazy="selectin", foreign_keys=[donor_surface_id]
    )
    recipient_surface_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("surface.id", ondelete="SET NULL")
    )
    recipient_surface: Mapped[Optional["Surface"]] = relationship(
        lazy="selectin", foreign_keys=[recipient_surface_id]
    )
    duration: Mapped[Optional[str]]
    pressure: Mapped[Optional[str]]
    friction_applied: Mapped[Optional[str]]
    contact_area: Mapped[Optional[str]]
    description_of_contact: Mapped[Optional[str]]
    activity_category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("activity_category.id", ondelete="SET NULL")
    )
    activity_category: Mapped[Optional["ActivityCategory"]] = relationship(
        lazy="selectin", foreign_keys=[activity_category_id]
    )
    condition_during_contact_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("condition_during_contact.id", ondelete="SET NULL")
    )
    condition_during_contact: Mapped[Optional["ConditionDuringContact"]] = relationship(
        lazy="selectin", foreign_keys=[condition_during_contact_id]
    )


from app.models.surface import Surface
from app.models.activity_category import ActivityCategory
from app.models.condition_during_contact import ConditionDuringContact
