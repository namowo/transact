import uuid
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.sql import text

from app.core.db import Base


class PCR(Base):
    __tablename__ = "pcr"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True,
        server_default=text("gen_random_uuid()")
    )
    result_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("result.id", ondelete="CASCADE")
    )
    dna_quantity: Mapped[Optional[float]]
    pcr_method_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("pcr_method.id", ondelete="SET NULL")
    )
    pcr_method: Mapped[Optional["PCRMethod"]] = relationship(
        lazy="selectin", foreign_keys=[pcr_method_id]
    )
    sample_input_volume_in_pcr: Mapped[Optional[float]]
    dna_input_amount_in_pcr: Mapped[Optional[float]]
    post_pcr_treatment_method_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("post_pcr_treatment_method.id", ondelete="SET NULL")
    )
    post_pcr_treatment_method: Mapped[Optional["PostPCRTreatmentMethod"]] = (
        relationship(lazy="selectin", foreign_keys=[post_pcr_treatment_method_id])
    )
    ce_method_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ce_method.id", ondelete="SET NULL")
    )
    ce_method: Mapped[Optional["CEMethod"]] = relationship(
        lazy="selectin", foreign_keys=[ce_method_id]
    )
    epg_analysis_method_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("epg_analysis_method.id", ondelete="SET NULL")
    )
    epg_analysis_method: Mapped[Optional["EPGAnalysisMethod"]] = relationship(
        lazy="selectin", foreign_keys=[epg_analysis_method_id]
    )
    epg_interpretation_method_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("epg_interpretation_method.id", ondelete="SET NULL")
    )
    epg_interpretation_method: Mapped[Optional["EPGInterpretationMethod"]] = (
        relationship(lazy="selectin", foreign_keys=[epg_interpretation_method_id])
    )
    no_of_contributors: Mapped[Optional[int]]
    mixture_proportion: Mapped[Optional[float]]
    total_rfu: Mapped[Optional[int]]
    total_no_of_alleles: Mapped[Optional[int]]


from app.models.pcr_method import PCRMethod
from app.models.post_pcr_treatment_method import PostPCRTreatmentMethod
from app.models.ce_method import CEMethod
from app.models.epg_analysis_method import EPGAnalysisMethod
from app.models.epg_interpretation_method import EPGInterpretationMethod
