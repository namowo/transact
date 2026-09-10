import uuid
from typing import Optional

from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from sqlalchemy.sql import text

from app.core.db import Base


class SkinDiseaseCategory(Base):
    __tablename__ = "skin_disease_category"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True,
        server_default=text("gen_random_uuid()")
    )
    name: Mapped[Optional[str]]
    influence_on_shedding_propensity: Mapped[Optional[bool]]
    # TODO Was genau ist mit literature gemeint? Welche Form von Daten sollen hier eingetragen werden?
    literature: Mapped[Optional[str]]
