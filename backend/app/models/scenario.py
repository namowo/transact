import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Table, Column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.sql import text

from app.core.db import Base

study_scenario = Table(
    "study_scenario",
    Base.metadata,
    Column("study_id", ForeignKey("study.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "scenario_id", ForeignKey("scenario.id", ondelete="CASCADE"), primary_key=True
    ),
)

scenario_persistence = Table(
    "scenario_persistence",
    Base.metadata,
    Column(
        "scenario_id", ForeignKey("scenario.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "persistence_id",
        ForeignKey("persistence.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Scenario(Base):
    __tablename__ = "scenario"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True,
        server_default=text("gen_random_uuid()")
    )
    realistic: Mapped[bool]
    scenario_category_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("scenario_category.id", ondelete="SET NULL")
    )
    scenario_category: Mapped["ScenarioCategory"] = relationship(
        lazy="selectin", foreign_keys=[scenario_category_id]
    )
    # The study this scenario was created for. Only this study may edit it;
    # other studies may link it to their own planning but see it read-only,
    # since it's a shared record.
    owning_study_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("study.id", ondelete="SET NULL")
    )
    owning_study: Mapped[Optional["Study"]] = relationship(
        lazy="selectin", foreign_keys=[owning_study_id]
    )
    studies: Mapped[list["Study"]] = relationship(
        lazy="selectin",
        secondary=study_scenario,
        back_populates="scenarios",
    )
    contact_templates: Mapped[list["ContactTemplate"]] = relationship(
        lazy="selectin",
        secondary="scenario_contact_template",
        back_populates="scenarios",
    )
    persistencies: Mapped[list["Persistence"]] = relationship(
        lazy="selectin",
        secondary=scenario_persistence,
        back_populates="scenarios",
    )


from app.models.scenario_category import ScenarioCategory
from app.models.study import Study
from app.models.contact_template import ContactTemplate
from app.models.persistence import Persistence
