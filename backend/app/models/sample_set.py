import uuid
from typing import Optional

from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.sql import text

from app.core.db import Base


class SampleSet(Base):
    """Groups samples that share the same attributes, to make data entry easier."""

    __tablename__ = "sample_set"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True,
        server_default=text("gen_random_uuid()")
    )
    name: Mapped[Optional[str]]
    # Not eager-loaded: nothing reads a set's samples, and loading them made
    # listing the sets fetch every sample with all its details.
    samples: Mapped[list["Sample"]] = relationship(
        lazy="select",
        back_populates="sample_set",
        foreign_keys="Sample.sample_set_id",
    )


from app.models.sample import Sample
