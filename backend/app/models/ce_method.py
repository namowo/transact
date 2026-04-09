from typing import Optional
from datetime import timedelta
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
    # TODO ebenfalls als Tabelle?
    ce_device: Mapped[Optional[str]]
    application_type: Mapped[Optional[str]]
    capillary_length: Mapped[Optional[int]]
    polymer: Mapped[Optional[str]]
    dye_set: Mapped[Optional[str]]
    oven_temperature: Mapped[Optional[float]]
    run_voltage: Mapped[Optional[float]]
    pre_run_voltage: Mapped[Optional[float]]
    injection_voltage: Mapped[Optional[float]]
    # TODO runtime klingt nach Laufzeit also Zeitangabe
    run_time: Mapped[Optional[timedelta]]
    pre_run_time: Mapped[Optional[timedelta]]
    injection_time: Mapped[Optional[timedelta]]
    type_of_formamide: Mapped[Optional[str]]
    volume_formamide: Mapped[Optional[int]]
    size_standard: Mapped[Optional[str]]
    volume_size_standard: Mapped[Optional[float]]
    input_volume_pcr_product: Mapped[Optional[float]]
    final_volume: Mapped[Optional[float]]


from app.models.laboratory import Laboratory
