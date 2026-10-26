import uuid
from typing import List, Optional

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
    # Reference only - the number of dye channels available for the
    # analytical-threshold rows below depends on which kit is used, but
    # there's no kit -> channel-count mapping yet, so rows are added manually.
    pcr_kit_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("pcr_kit.id", ondelete="SET NULL")
    )
    pcr_kit: Mapped[Optional["PCRKit"]] = relationship(
        lazy="selectin", foreign_keys=[pcr_kit_id]
    )
    dye_channel_thresholds: Mapped[List["EPGAnalysisMethodDyeChannelThreshold"]] = relationship(
        lazy="selectin",
        order_by="EPGAnalysisMethodDyeChannelThreshold.position",
        cascade="all, delete-orphan",
    )
    application_analytical_threshold: Mapped[Optional[str]]
    stutter_filter_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("stutter_filter.id", ondelete="SET NULL")
    )
    stutter_filter: Mapped[Optional["StutterFilter"]] = relationship(
        lazy="selectin", foreign_keys=[stutter_filter_id]
    )
    description: Mapped[Optional[str]]


from app.models.laboratory import Laboratory
from app.models.genotyping_software import GenotypingSoftware
from app.models.pcr_kit import PCRKit
from app.models.stutter_filter import StutterFilter
from app.models.epg_analysis_method_dye_channel_threshold import (
    EPGAnalysisMethodDyeChannelThreshold,
)
