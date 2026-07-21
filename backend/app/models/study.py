from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Study(Base):
    __tablename__ = "study"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    laboratory_id: Mapped[int] = mapped_column(
        ForeignKey("laboratory.id", ondelete="SET NULL")
    )
    laboratory: Mapped[Optional["Laboratory"]] = relationship(
        lazy="selectin", foreign_keys=[laboratory_id]
    )
    doi: Mapped[Optional[str]]
    authors: Mapped[list["Author"]] = relationship(
        lazy="selectin", cascade="all, delete-orphan", order_by="Author.position"
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
    quality_checked_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL")
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
        back_populates="study",
        cascade="all, delete-orphan",
        foreign_keys="Scenario.study_id",
    )


from app.models.author import Author
from app.models.laboratory import Laboratory
from app.models.user import User
