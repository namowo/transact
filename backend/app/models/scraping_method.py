from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ScrapingMethod(Base):
    __tablename__ = "scraping_method"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    scraping_device: Mapped[Optional[str]]

    scraping_device_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("scraping_device.id", ondelete="SET NULL")
    )
    scraping_device: Mapped[Optional["ScrapingDevice"]] = relationship(
        lazy="selectin", foreign_keys=[scraping_device_id]
    )
    description: Mapped[Optional[str]]
    catalogue_number_of_supplier: Mapped[Optional[str]]
    full_name_as_by_supplier: Mapped[Optional[str]]
    supplier: Mapped[Optional[str]]


from app.models.scraping_device import ScrapingDevice
