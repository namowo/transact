from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class PCRMethod(Base):
    __tablename__ = "pcr_method"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    laboratory_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("laboratory.id", ondelete="SET NULL")
    )
    laboratory: Mapped[Optional["Laboratory"]] = relationship(
        lazy="selectin", foreign_keys=[laboratory_id]
    )
    pcr_kit: Mapped[Optional[str]]
    thermocycler: Mapped[Optional[str]]
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


from app.models.laboratory import Laboratory
