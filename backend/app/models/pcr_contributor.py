import uuid
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.sql import text

from app.core.db import Base


class PCRContributor(Base):
    __tablename__ = "pcr_contributor"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True,
        server_default=text("gen_random_uuid()")
    )
    pcr_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("pcr.id", ondelete="CASCADE")
    )
    individual_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("individual.id", ondelete="SET NULL")
    )
    individual: Mapped[Optional["Individual"]] = relationship(
        lazy="selectin", foreign_keys=[individual_id]
    )
    # Set when this contributor is an unknown person rather than a known
    # Individual - e.g. "UP1", "UP2". Mutually exclusive with individual_id.
    unknown_label: Mapped[Optional[str]]
    mixture_proportion: Mapped[Optional[float]]


from app.models.individual import Individual
