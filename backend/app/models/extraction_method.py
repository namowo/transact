import uuid
from typing import List, Optional
from datetime import timedelta
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.sql import text

from app.core.db import Base


class ExtractionMethod(Base):
    __tablename__ = "extraction_method"

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
    principle_of_extraction_method_category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("principle_of_extraction_method_category.id", ondelete="SET NULL")
    )
    principle_of_extraction_method_category: Mapped[
        Optional["PrincipleOfExtractionMethodCategory"]
    ] = relationship(
        lazy="selectin", foreign_keys=[principle_of_extraction_method_category_id]
    )
    extraction_protocol: Mapped[Optional[str]]
    extraction_platform_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("platform.id", ondelete="SET NULL")
    )
    extraction_platform: Mapped[Optional["Platform"]] = relationship(
        lazy="selectin", foreign_keys=[extraction_platform_id]
    )
    lysis_buffer_components: Mapped[List["ExtractionMethodLysisBufferComponent"]] = relationship(
        lazy="selectin",
        order_by="ExtractionMethodLysisBufferComponent.position",
        cascade="all, delete-orphan",
    )
    lysis_incubation_time: Mapped[Optional[timedelta]]
    lysis_incubation_temperature: Mapped[Optional[float]]
    thermoshaker_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("thermoshaker.id", ondelete="SET NULL")
    )
    thermoshaker: Mapped[Optional["Thermoshaker"]] = relationship(
        lazy="selectin", foreign_keys=[thermoshaker_id]
    )
    rcf: Mapped[Optional[float]]
    volume_of_lysate_used_for_extraction: Mapped[Optional[float]]
    application_of_further_purification_step: Mapped[Optional[bool]]
    description_of_further_purification_step: Mapped[Optional[str]]
    abbreviations_to_manufacturers_protocol: Mapped[Optional[str]]


from app.models.laboratory import Laboratory
from app.models.principle_of_extraction_method_category import (
    PrincipleOfExtractionMethodCategory,
)
from app.models.platform import Platform
from app.models.thermoshaker import Thermoshaker
from app.models.extraction_method_lysis_buffer_component import (
    ExtractionMethodLysisBufferComponent,
)
