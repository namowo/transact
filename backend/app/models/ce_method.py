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
    ce_device_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("ce_device.id", ondelete="SET NULL")
    )
    ce_device: Mapped[Optional["CEDevice"]] = relationship(
        lazy="selectin", foreign_keys=[ce_device_id]
    )
    application_type: Mapped[Optional[str]]
    capillary_length: Mapped[Optional[int]]
    polymer_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("polymer.id", ondelete="SET NULL")
    )
    polymer: Mapped[Optional["Polymer"]] = relationship(
        lazy="selectin", foreign_keys=[polymer_id]
    )
    dye_set_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("dye_set.id", ondelete="SET NULL")
    )
    dye_set: Mapped[Optional["DyeSet"]] = relationship(
        lazy="selectin", foreign_keys=[dye_set_id]
    )
    oven_temperature: Mapped[Optional[float]]
    run_voltage: Mapped[Optional[float]]
    pre_run_voltage: Mapped[Optional[float]]
    injection_voltage: Mapped[Optional[float]]
    # TODO runtime klingt nach Laufzeit also Zeitangabe
    run_time: Mapped[Optional[timedelta]]
    pre_run_time: Mapped[Optional[timedelta]]
    injection_time: Mapped[Optional[timedelta]]
    type_of_formamide_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("type_of_formamide.id", ondelete="SET NULL")
    )
    type_of_formamide: Mapped[Optional["TypeOfFormamide"]] = relationship(
        lazy="selectin", foreign_keys=[type_of_formamide_id]
    )
    volume_formamide: Mapped[Optional[int]]
    size_standard_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("size_standard.id", ondelete="SET NULL")
    )
    size_standard: Mapped[Optional["SizeStandard"]] = relationship(
        lazy="selectin", foreign_keys=[size_standard_id]
    )
    volume_size_standard: Mapped[Optional[float]]
    input_volume_pcr_product: Mapped[Optional[float]]
    final_volume: Mapped[Optional[float]]


from app.models.laboratory import Laboratory
from app.models.ce_device import CEDevice
from app.models.polymer import Polymer
from app.models.dye_set import DyeSet
from app.models.type_of_formamide import TypeOfFormamide
from app.models.size_standard import SizeStandard
