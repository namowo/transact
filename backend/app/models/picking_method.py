from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class PickingMethod(Base):
    __tablename__ = "picking_method"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    picking_device_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("picking_device.id", ondelete="SET NULL")
    )
    picking_device: Mapped[Optional["PickingDevice"]] = relationship(
        lazy="selectin", foreign_keys=[picking_device_id]
    )
    description: Mapped[Optional[str]]
    catalogue_number_of_supplier: Mapped[Optional[str]]
    full_name_as_by_supplier: Mapped[Optional[str]]
    supplier: Mapped[Optional[str]]


from app.models.picking_device import PickingDevice
