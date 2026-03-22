from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class ExtractionMethod(Base):
    __tablename__ = "extraction_method"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    laboratory_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("laboratory.id", ondelete="SET NULL")
    )
    laboratory: Mapped[Optional["Laboratory"]] = relationship(
        lazy="selectin", foreign_keys=[laboratory_id]
    )
    principle_of_extraction_method_category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("principle_of_extraction_method_category.id", ondelete="SET NULL")
    )
    principle_of_extraction_method_category: Mapped[Optional["PrincipleOfExtractionMethodCategory"]] = relationship(
        lazy="selectin", foreign_keys=[principle_of_extraction_method_category_id]
    )
    extraction_protocol: Mapped[Optional[str]]
    extraction_platform: Mapped[Optional[str]]
    additional_lysis_buffer_components: Mapped[Optional[str]]
    volume_lysis_buffer_components: Mapped[Optional[int]]
    lysis_incubation_time: Mapped[Optional[int]]
    lysis_incubation_temperature: Mapped[Optional[int]]
    volume_of_lysate_used_for_extraction: Mapped[Optional[int]]
    application_of_further_purification_step: Mapped[Optional[bool]]
    description_of_further_purification_step: Mapped[Optional[str]]


from app.models.laboratory import Laboratory
from app.models.principle_of_extraction_method_category import PrincipleOfExtractionMethodCategory
