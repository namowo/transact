from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class CuttingMethod(Base):
    __tablename__ = "cutting_method"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    cutting_device_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("cutting_device.id", ondelete="SET NULL")
    )
    cutting_device: Mapped[Optional["TypeOfTape"]] = relationship(
        lazy="selectin", foreign_keys=[cutting_device_id]
    )
    description: Mapped[Optional[str]]
    catalogue_number_of_supplier: Mapped[Optional[str]]
    full_name_as_by_supplier: Mapped[Optional[str]]
    # TODO Macht es Sinn die Supplier auch in eine eigene Tabelle zu überführen?
    supplier: Mapped[Optional[str]]


from app.models.cutting_device import CuttingDevice
