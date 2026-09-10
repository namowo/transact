import uuid
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.sql import text

from app.core.db import Base


class EPGAnalysisMethod(Base):
    __tablename__ = "epg_analysis_method"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True,
        server_default=text("gen_random_uuid()")
    )
    laboratory_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("laboratory.id", ondelete="SET NULL")
    )
    laboratory: Mapped[Optional["Laboratory"]] = relationship(
        lazy="selectin", foreign_keys=[laboratory_id]
    )
    genotyping_software_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("genotyping_software.id", ondelete="SET NULL")
    )
    genotyping_software: Mapped[Optional["GenotypingSoftware"]] = relationship(
        lazy="selectin", foreign_keys=[genotyping_software_id]
    )
    analytical_threshold: Mapped[Optional[int]]
    application_analytical_threshold: Mapped[Optional[str]]
    stutter_filter: Mapped[Optional[str]]


from app.models.laboratory import Laboratory
from app.models.genotyping_software import GenotypingSoftware
