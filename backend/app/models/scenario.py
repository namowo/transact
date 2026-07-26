from sqlalchemy import ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

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

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    realistic: Mapped[bool]
    scenario_category_id: Mapped[int] = mapped_column(
        ForeignKey("scenario_category.id", ondelete="SET NULL")
    )
    scenario_category: Mapped["ScenarioCategory"] = relationship(
        lazy="selectin", foreign_keys=[scenario_category_id]
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
