from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class PostPCRTreatmentMethod(Base):
    __tablename__ = "post_pcr_treatment_method"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    laboratory_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("laboratory.id", ondelete="SET NULL")
    )
    laboratory: Mapped[Optional["Laboratory"]] = relationship(
        lazy="selectin", foreign_keys=[laboratory_id]
    )
    application_of_post_pcr_purification_step: Mapped[Optional[bool]]
    description_of_post_pcr_purification_step: Mapped[Optional[str]]
    dilution_of_pcr_product: Mapped[Optional[bool]]
    dilution_factor: Mapped[Optional[float]]


from app.models.laboratory import Laboratory
