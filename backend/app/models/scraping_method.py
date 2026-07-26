from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class ScrapingMethod(Base):
    __tablename__ = "scraping_method"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    scraping_device_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("scraping_device.id", ondelete="SET NULL")
    )
    scraping_device: Mapped[Optional["ScrapingDevice"]] = relationship(
        lazy="selectin", foreign_keys=[scraping_device_id]
    )
    description: Mapped[Optional[str]]
    supplier_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("supplier.id", ondelete="SET NULL")
    )
    supplier: Mapped[Optional["Supplier"]] = relationship(
        lazy="selectin", foreign_keys=[supplier_id]
    )


from app.models.scraping_device import ScrapingDevice
from app.models.supplier import Supplier
