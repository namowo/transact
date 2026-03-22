from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class CEMethod(Base):
    __tablename__ = "ce_method"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    laboratory_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("laboratory.id", ondelete="SET NULL")
    )
    laboratory: Mapped[Optional["Laboratory"]] = relationship(
        lazy="selectin", foreign_keys=[laboratory_id]
    )
    ce_device: Mapped[Optional[str]]
    initial_denaturation_temp: Mapped[Optional[int]]
    initial_denaturation_time: Mapped[Optional[int]]
    no_of_cycles: Mapped[Optional[int]]
    denaturation_temp: Mapped[Optional[int]]
    denaturation_time: Mapped[Optional[int]]
    annealing_temp: Mapped[Optional[int]]
    annealing_time: Mapped[Optional[int]]
    elongation_temp: Mapped[Optional[int]]
    elongation_time: Mapped[Optional[int]]
    final_elongation_temp: Mapped[Optional[int]]
    final_elongation_time: Mapped[Optional[int]]
    ramping: Mapped[Optional[int]]
    total_volume_pcr_reaction: Mapped[Optional[int]]
    application_type: Mapped[Optional[str]]
    capillary_length: Mapped[Optional[str]]
    polymer: Mapped[Optional[str]]
    dye_set: Mapped[Optional[str]]
    oven_temperature: Mapped[Optional[str]]
    run_voltage: Mapped[Optional[str]]
    pre_run_voltage: Mapped[Optional[str]]
    injection_voltage: Mapped[Optional[str]]
    run_time: Mapped[Optional[str]]
    pre_run_time: Mapped[Optional[str]]
    injection_time: Mapped[Optional[str]]
    type_of_formamide: Mapped[Optional[str]]
    volume_formamide: Mapped[Optional[str]]
    size_standard: Mapped[Optional[str]]
    volume_size_standard: Mapped[Optional[str]]
    input_volume_pcr_product: Mapped[Optional[str]]
    final_volume: Mapped[Optional[str]]


from app.models.laboratory import Laboratory
