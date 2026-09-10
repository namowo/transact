import uuid
from typing import Optional
from datetime import timedelta

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.sql import text

from app.core.db import Base


class Persistence(Base):
    __tablename__ = "persistence"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True,
        server_default=text("gen_random_uuid()")
    )
    # The study this persistence was created for. Only this study may edit
    # it; other studies may link it via a scenario but see it read-only,
    # since it's a shared record.
    owning_study_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("study.id", ondelete="SET NULL")
    )
    owning_study: Mapped[Optional["Study"]] = relationship(
        lazy="selectin", foreign_keys=[owning_study_id]
    )
    # Optional label to tell apart multiple persistencies on the same
    # scenario, e.g. "Winter" vs "Summer".
    name: Mapped[Optional[str]]
    interval_of_persistence: Mapped[Optional[float]]
    temperature: Mapped[Optional[float]]
    humidity: Mapped[Optional[float]]
    uv_irradiation: Mapped[Optional[float]]
    indoors: Mapped[Optional[bool]]
    change_over_time: Mapped[Optional[bool]]
    duration_of_disturbance: Mapped[Optional[timedelta]]
    description_of_disturbance: Mapped[Optional[str]]
    disturbance_category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("disturbance_category.id", ondelete="SET NULL")
    )
    disturbance_category: Mapped[Optional["DisturbanceCategory"]] = relationship(
        lazy="selectin", foreign_keys=[disturbance_category_id]
    )
    geographic_location_category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("geographic_location_category.id", ondelete="SET NULL")
    )
    geographic_location_category: Mapped[Optional["GeographicLocationCategory"]] = (
        relationship(lazy="selectin", foreign_keys=[geographic_location_category_id])
    )
    scenarios: Mapped[list["Scenario"]] = relationship(
        lazy="selectin",
        secondary="scenario_persistence",
        back_populates="persistencies",
    )


from app.models.disturbance_category import DisturbanceCategory
from app.models.geographic_location_category import GeographicLocationCategory
from app.models.study import Study
