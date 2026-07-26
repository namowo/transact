from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class CuttingMethod(Base):
    __tablename__ = "cutting_method"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    cutting_device_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("cutting_device.id", ondelete="SET NULL")
    )
    cutting_device: Mapped[Optional["CuttingDevice"]] = relationship(
        lazy="selectin", foreign_keys=[cutting_device_id]
    )
    description: Mapped[Optional[str]]
    supplier_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("supplier.id", ondelete="SET NULL")
    )
    supplier: Mapped[Optional["Supplier"]] = relationship(
        lazy="selectin", foreign_keys=[supplier_id]
    )


from app.models.cutting_device import CuttingDevice
from app.models.supplier import Supplier
