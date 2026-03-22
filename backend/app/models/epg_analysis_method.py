from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class EPGAnalysisMethod(Base):
    __tablename__ = "epg_analysis_method"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    laboratory_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("laboratory.id", ondelete="SET NULL")
    )
    laboratory: Mapped[Optional["Laboratory"]] = relationship(
        lazy="selectin", foreign_keys=[laboratory_id]
    )
    genotyping_software: Mapped[Optional[str]]
    analytical_threshold: Mapped[Optional[int]]
    application_analytical_threshold: Mapped[Optional[str]]
    stutter_filter: Mapped[Optional[str]]


from app.models.laboratory import Laboratory
