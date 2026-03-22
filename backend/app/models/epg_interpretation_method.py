from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class EPGInterpretationMethod(Base):
    __tablename__ = "epg_interpretation_method"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    laboratory_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("laboratory.id", ondelete="SET NULL")
    )
    laboratory: Mapped[Optional["Laboratory"]] = relationship(
        lazy="selectin", foreign_keys=[laboratory_id]
    )
    determination_of_noc: Mapped[Optional[str]]
    statistical_software: Mapped[Optional[str]]
    parameters_modelled_by_software: Mapped[Optional[str]]
    allele_frequency_database: Mapped[Optional[str]]


from app.models.laboratory import Laboratory
