from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class VacuumMethod(Base):
    __tablename__ = "vacuum_method"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    vacuum_device_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("vaccum_device.id", ondelete="SET NULL")
    )
    vacuum_device: Mapped[Optional["VacuumDevice"]] = relationship(
        lazy="selectin", foreign_keys=[vacuum_device_id]
    )
    description: Mapped[Optional[str]]
    catalogue_number_of_supplier: Mapped[Optional[str]]
    full_name_as_by_supplier: Mapped[Optional[str]]
    supplier: Mapped[Optional[str]]


from app.models.vacuum_device import VacuumDevice
