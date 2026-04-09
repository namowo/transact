from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


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
    study_id: Mapped[int] = mapped_column(ForeignKey("study.id", ondelete="SET NULL"))
    study: Mapped["Study"] = relationship(lazy="selectin", foreign_keys=[study_id])
    contact_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("contact.id", ondelete="SET NULL")
    )
    contact: Mapped[Optional["Contact"]] = relationship(
        lazy="selectin", foreign_keys=[contact_id]
    )
    persistence_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("persistence.id", ondelete="SET NULL")
    )
    persistence: Mapped[Optional["Persistence"]] = relationship(
        lazy="selectin", foreign_keys=[persistence_id]
    )


from app.models.scenario_category import ScenarioCategory
from app.models.study import Study
from app.models.contact import Contact
from app.models.persistence import Persistence
