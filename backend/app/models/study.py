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
    # TODO Authors in separate Tables?
    authors: Mapped[Optional[str]]
    description: Mapped[Optional[str]]
    year: Mapped[Optional[str]]
    title: Mapped[str]
    abstract: Mapped[Optional[str]]
    journal: Mapped[Optional[str]]
    # TODO Foreign key for plan_a_tranfer_experiment or add_data_to_repository. These are XOR
    type: Mapped[int]
    plan_a_transfer_experiment: Mapped[Optional[bool]]
    add_data_to_repository: Mapped[Optional[bool]]
    quality_check_passed: Mapped[Optional[bool]]
    # TODO should be part of the author table
    corresponding_author_contact: Mapped[Optional[str]]


from app.models.laboratory import Laboratory
