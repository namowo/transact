from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Recovery(Base):
    __tablename__ = "recovery"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    study_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("study.id", ondelete="SET NULL")
    )
    study: Mapped[Optional["Study"]] = relationship(
        lazy="selectin", back_populates="recoveries", foreign_keys=[study_id]
    )
    recovery_set_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("recovery_set.id", ondelete="SET NULL")
    )
    recovery_set: Mapped[Optional["RecoverySet"]] = relationship(
        lazy="selectin", back_populates="recoveries", foreign_keys=[recovery_set_id]
    )
    surface_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("surface.id", ondelete="SET NULL")
    )
    surface: Mapped[Optional["Surface"]] = relationship(
        lazy="selectin", foreign_keys=[surface_id]
    )
    sampling_method_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sampling_method.id", ondelete="SET NULL")
    )
    sampling_method: Mapped[Optional["SamplingMethod"]] = relationship(
        lazy="selectin", foreign_keys=[sampling_method_id]
    )
    extraction_method_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("extraction_method.id", ondelete="SET NULL")
    )
    extraction_method: Mapped[Optional["ExtractionMethod"]] = relationship(
        lazy="selectin", foreign_keys=[extraction_method_id]
    )
    elution_volume: Mapped[Optional[float]]
    area: Mapped[Optional[float]]

    experience_level_of_sampler_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("experience_level.id", ondelete="SET NULL")
    )
    experience_level_of_sampler: Mapped[Optional["ExperienceLevel"]] = relationship(
        lazy="selectin", foreign_keys=[experience_level_of_sampler_id]
    )


from app.models.surface import Surface
from app.models.sampling_method import SamplingMethod
from app.models.extraction_method import ExtractionMethod
from app.models.experience_level import ExperienceLevel
from app.models.study import Study
from app.models.recovery_set import RecoverySet
