import uuid
from typing import Optional

from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from sqlalchemy.sql import text

from app.core.db import Base


class ApplicationAnalyticalThreshold(Base):
    __tablename__ = "application_analytical_threshold"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True,
        server_default=text("gen_random_uuid()")
    )
    name: Mapped[Optional[str]]
