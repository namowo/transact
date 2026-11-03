import uuid
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.sql import text

from app.core.db import Base


class EPGAnalysisMethodDyeChannelThreshold(Base):
    __tablename__ = "epg_analysis_method_dye_channel_threshold"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True,
        server_default=text("gen_random_uuid()")
    )
    epg_analysis_method_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("epg_analysis_method.id", ondelete="CASCADE"),
    )
    dye_channel_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dye_channel.id", ondelete="SET NULL"),
    )
    dye_channel: Mapped[Optional["DyeChannel"]] = relationship(
        lazy="selectin", foreign_keys=[dye_channel_id]
    )
    analytical_threshold: Mapped[Optional[float]]
    # Preserves the row order as entered.
    position: Mapped[int]


from app.models.dye_channel import DyeChannel
