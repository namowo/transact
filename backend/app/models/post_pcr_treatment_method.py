import uuid
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.sql import text

from app.core.db import Base


class PostPCRTreatmentMethod(Base):
    __tablename__ = "post_pcr_treatment_method"

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
    application_of_post_pcr_purification_step: Mapped[Optional[bool]]
    description_of_post_pcr_purification_step: Mapped[Optional[str]]
    dilution_of_pcr_product: Mapped[Optional[bool]]
    dilution_factor: Mapped[Optional[float]]


from app.models.laboratory import Laboratory
