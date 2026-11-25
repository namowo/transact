import uuid
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.sql import text

from app.core.db import Base


class Result(Base):
    __tablename__ = "result"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True,
        server_default=text("gen_random_uuid()")
    )
    quantification_method_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("quantification_method.id", ondelete="SET NULL")
    )
    quantification_method: Mapped[Optional["QuantificationMethod"]] = relationship(
        lazy="selectin", foreign_keys=[quantification_method_id]
    )
    sample_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sample.id", ondelete="SET NULL")
    )
    sample: Mapped[Optional["Sample"]] = relationship(
        lazy="selectin", foreign_keys=[sample_id]
    )
    dna_concentration: Mapped[Optional[float]]
    degradation_index: Mapped[Optional[float]]
    inhibition_category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("inhibition_category.id", ondelete="SET NULL")
    )
    inhibition_category: Mapped[Optional["InhibitionCategory"]] = relationship(
        lazy="selectin", foreign_keys=[inhibition_category_id]
    )
    pcrs: Mapped[list["PCR"]] = relationship(
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="PCR.id",
    )


from app.models.inhibition_category import InhibitionCategory
from app.models.quantification_method import QuantificationMethod
from app.models.sample import Sample
from app.models.pcr import PCR
