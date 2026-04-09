from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class PickingDevice(Base):
    __tablename__ = "picking_device"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    name: Mapped[Optional[str]]
    description: Mapped[Optional[str]]
