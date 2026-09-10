import uuid
from typing import Optional
from datetime import timedelta

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.sql import text

from app.core.db import Base


class Contact(Base):
    """An actual, realized instance of a ContactTemplate."""

    __tablename__ = "contact"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True,
        server_default=text("gen_random_uuid()")
    )
    contact_template_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("contact_template.id", ondelete="CASCADE")
    )
    contact_template: Mapped["ContactTemplate"] = relationship(
        lazy="selectin",
        back_populates="contacts",
        foreign_keys=[contact_template_id],
    )
    donor_surface_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("surface.id", ondelete="SET NULL")
    )
    donor_surface: Mapped[Optional["Surface"]] = relationship(
        lazy="selectin", foreign_keys=[donor_surface_id]
    )
    recipient_surface_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("surface.id", ondelete="SET NULL")
    )
    recipient_surface: Mapped[Optional["Surface"]] = relationship(
        lazy="selectin", foreign_keys=[recipient_surface_id]
    )
    # The following override the corresponding ContactTemplate attribute when set;
    # a null value means the template's value applies.
    duration: Mapped[Optional[timedelta]]
    pressure: Mapped[Optional[float]]
    pressure_estimate_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("pressure_estimate.id", ondelete="SET NULL")
    )
    pressure_estimate: Mapped[Optional["PressureEstimate"]] = relationship(
        lazy="selectin", foreign_keys=[pressure_estimate_id]
    )
    friction_applied: Mapped[Optional[float]]
    friction_applied_estimate_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("friction_applied_estiamte.id", ondelete="SET NULL")
    )
    friction_applied_estimate: Mapped[Optional["FrictionAppliedEstimate"]] = (
        relationship(lazy="selectin", foreign_keys=[friction_applied_estimate_id])
    )
    contact_area: Mapped[Optional[float]]
    description_of_contact: Mapped[Optional[str]]
    activity_category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("activity_category.id", ondelete="SET NULL")
    )
    activity_category: Mapped[Optional["ActivityCategory"]] = relationship(
        lazy="selectin", foreign_keys=[activity_category_id]
    )
    condition_during_contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("condition_during_contact.id", ondelete="SET NULL")
    )
    condition_during_contact: Mapped[Optional["ConditionDuringContact"]] = relationship(
        lazy="selectin", foreign_keys=[condition_during_contact_id]
    )


from app.models.surface import Surface
from app.models.pressure_estimate import PressureEstimate
from app.models.friction_applied_estimate import FrictionAppliedEstimate
from app.models.activity_category import ActivityCategory
from app.models.condition_during_contact import ConditionDuringContact
