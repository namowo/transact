import uuid
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.sql import text

from app.core.db import Base


class ExtractionMethodLysisBufferComponent(Base):
    __tablename__ = "extraction_method_lysis_buffer_component"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True,
        server_default=text("gen_random_uuid()")
    )
    extraction_method_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("extraction_method.id", ondelete="CASCADE"),
    )
    lysis_buffer_component_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lysis_buffer_component.id", ondelete="SET NULL"),
    )
    lysis_buffer_component: Mapped[Optional["LysisBufferComponent"]] = relationship(
        lazy="selectin", foreign_keys=[lysis_buffer_component_id]
    )
    volume: Mapped[Optional[float]]
    # Preserves the row order as entered.
    position: Mapped[int]


from app.models.lysis_buffer_component import LysisBufferComponent
