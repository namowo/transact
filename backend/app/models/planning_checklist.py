import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class PlanningChecklist(Base):
    """A laboratory's own planning checklist. Laboratories without one use
    the default checklist (app/services/planning_checklist.py)."""

    __tablename__ = "planning_checklist"

    laboratory_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("laboratory.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # [{"title": str, "items": [str, ...]}, ...]
    sections: Mapped[list] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
