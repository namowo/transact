from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class VacuumMethod(Base):
    __tablename__ = "vacuum_method"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    vacuum_device_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("vacuum_device.id", ondelete="SET NULL")
    )
    vacuum_device: Mapped[Optional["VacuumDevice"]] = relationship(
        lazy="selectin", foreign_keys=[vacuum_device_id]
    )
    description: Mapped[Optional[str]]
    supplier_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("supplier.id", ondelete="SET NULL")
    )
    supplier: Mapped[Optional["Supplier"]] = relationship(
        lazy="selectin", foreign_keys=[supplier_id]
    )


from app.models.vacuum_device import VacuumDevice
from app.models.supplier import Supplier
