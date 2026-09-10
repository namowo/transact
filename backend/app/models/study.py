import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.sql import text

from app.core.db import Base


class Study(Base):
    __tablename__ = "study"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True,
        server_default=text("gen_random_uuid()")
    )
    laboratory_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("laboratory.id", ondelete="SET NULL")
    )
    laboratory: Mapped[Optional["Laboratory"]] = relationship(
        lazy="selectin", foreign_keys=[laboratory_id]
    )
    doi: Mapped[Optional[str]]
    study_authors: Mapped[list["StudyAuthor"]] = relationship(
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="StudyAuthor.position",
    )
    description: Mapped[Optional[str]]
    year: Mapped[Optional[str]]
    title: Mapped[str]
    abstract: Mapped[Optional[str]]
    journal: Mapped[Optional[str]]
    plan_a_transfer_experiment: Mapped[Optional[bool]]
    add_data_to_repository: Mapped[Optional[bool]]
    quality_check_passed: Mapped[Optional[bool]]
    published: Mapped[Optional[bool]]
    quality_checked_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL")
    )
    quality_checked_by: Mapped[Optional["User"]] = relationship(
        lazy="selectin", foreign_keys=[quality_checked_by_id]
    )
    quality_checked_at: Mapped[Optional[datetime]]
    corresponding_author_name: Mapped[Optional[str]]
    corresponding_author_email: Mapped[Optional[str]]
    corresponding_author_phone: Mapped[Optional[str]]
    scenarios: Mapped[list["Scenario"]] = relationship(
        lazy="selectin",
        secondary="study_scenario",
        back_populates="studies",
    )
    recoveries: Mapped[list["Recovery"]] = relationship(
        lazy="selectin",
        back_populates="study",
        cascade="all, delete-orphan",
        foreign_keys="Recovery.study_id",
    )

    @property
    def authors(self) -> list["Author"]:
        return [study_author.author for study_author in self.study_authors]


from app.models.author import Author
from app.models.laboratory import Laboratory
from app.models.study_author import StudyAuthor
from app.models.user import User
