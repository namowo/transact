import uuid
from typing import Optional
from datetime import timedelta
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.sql import text

from app.core.db import Base


class PCRMethod(Base):
    __tablename__ = "pcr_method"

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
    pcr_kit_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("pcr_kit.id", ondelete="SET NULL")
    )
    pcr_kit: Mapped[Optional["PCRKit"]] = relationship(
        lazy="selectin", foreign_keys=[pcr_kit_id]
    )
    thermocycler_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("thermocycler.id", ondelete="SET NULL")
    )
    thermocycler: Mapped[Optional["Thermocycler"]] = relationship(
        lazy="selectin", foreign_keys=[thermocycler_id]
    )
    initial_denaturation_temp: Mapped[Optional[float]]
    initial_denaturation_time: Mapped[Optional[timedelta]]
    no_of_cycles: Mapped[Optional[int]]
    denaturation_temp: Mapped[Optional[float]]
    denaturation_time: Mapped[Optional[timedelta]]
    annealing_temp: Mapped[Optional[float]]
    annealing_time: Mapped[Optional[timedelta]]
    elongation_temp: Mapped[Optional[float]]
    elongation_time: Mapped[Optional[timedelta]]
    final_elongation_temp: Mapped[Optional[float]]
    final_elongation_time: Mapped[Optional[timedelta]]
    ramping: Mapped[Optional[float]]
    total_volume_pcr_reaction: Mapped[Optional[float]]


from app.models.laboratory import Laboratory
from app.models.pcr_kit import PCRKit
from app.models.thermocycler import Thermocycler
