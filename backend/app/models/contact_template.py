import uuid
from typing import Optional
from datetime import timedelta

from sqlalchemy import ForeignKey, Table, Column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.sql import text

from app.core.db import Base

scenario_contact_template = Table(
    "scenario_contact_template",
    Base.metadata,
    Column(
        "scenario_id", ForeignKey("scenario.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "contact_template_id",
        ForeignKey("contact_template.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class ContactTemplate(Base):
    """Plannable, scenario-level definition of a contact between a donor and recipient surface."""

    __tablename__ = "contact_template"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True,
        server_default=text("gen_random_uuid()")
    )
    scenarios: Mapped[list["Scenario"]] = relationship(
        lazy="selectin",
        secondary=scenario_contact_template,
        back_populates="contact_templates",
    )
    donor_surface_template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("surface_template.id", ondelete="SET NULL")
    )
    donor_surface_template: Mapped[Optional["SurfaceTemplate"]] = relationship(
        lazy="selectin", foreign_keys=[donor_surface_template_id]
    )
    recipient_surface_template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("surface_template.id", ondelete="SET NULL")
    )
    recipient_surface_template: Mapped[Optional["SurfaceTemplate"]] = relationship(
        lazy="selectin", foreign_keys=[recipient_surface_template_id]
    )
    duration: Mapped[Optional[timedelta]]
    pressure_estimate_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("pressure_estimate.id", ondelete="SET NULL")
    )
    pressure_estimate: Mapped[Optional["PressureEstimate"]] = relationship(
        lazy="selectin", foreign_keys=[pressure_estimate_id]
    )
    friction_applied_estimate_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("friction_applied_estiamte.id", ondelete="SET NULL")
    )
    friction_applied_estimate: Mapped[Optional["FrictionAppliedEstimate"]] = (
        relationship(lazy="selectin", foreign_keys=[friction_applied_estimate_id])
    )
    # TODO What is contact area?
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
    contacts: Mapped[list["Contact"]] = relationship(
        lazy="selectin",
        back_populates="contact_template",
        cascade="all, delete-orphan",
        foreign_keys="Contact.contact_template_id",
    )


from app.models.surface_template import SurfaceTemplate
from app.models.pressure_estimate import PressureEstimate
from app.models.friction_applied_estimate import FrictionAppliedEstimate
from app.models.activity_category import ActivityCategory
from app.models.condition_during_contact import ConditionDuringContact
from app.models.contact import Contact
