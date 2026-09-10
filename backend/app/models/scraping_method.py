import uuid
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.sql import text

from app.core.db import Base


class ScrapingMethod(Base):
    __tablename__ = "scraping_method"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True,
        server_default=text("gen_random_uuid()")
    )
    scraping_device_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("scraping_device.id", ondelete="SET NULL")
    )
    scraping_device: Mapped[Optional["ScrapingDevice"]] = relationship(
        lazy="selectin", foreign_keys=[scraping_device_id]
    )
    description: Mapped[Optional[str]]
    supplier_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("supplier.id", ondelete="SET NULL")
    )
    supplier: Mapped[Optional["Supplier"]] = relationship(
        lazy="selectin", foreign_keys=[supplier_id]
    )


from app.models.scraping_device import ScrapingDevice
from app.models.supplier import Supplier
