import uuid
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.sql import text

from app.core.db import Base


class SamplingMethod(Base):
    __tablename__ = "sampling_method"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True,
        server_default=text("gen_random_uuid()")
    )
    laboratory_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("laboratory.id", ondelete="SET NULL")
    )
    laboratory: Mapped[Optional["Laboratory"]] = relationship(
        lazy="selectin", foreign_keys=[laboratory_id]
    )
    swab_method_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("swab_method.id", ondelete="SET NULL")
    )
    swab_method: Mapped[Optional["SwabMethod"]] = relationship(
        lazy="selectin", foreign_keys=[swab_method_id]
    )
    tape_method_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tape_method.id", ondelete="SET NULL")
    )
    tape_method: Mapped[Optional["TapeMethod"]] = relationship(
        lazy="selectin", foreign_keys=[tape_method_id]
    )
    vacuum_method_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("vacuum_method.id", ondelete="SET NULL")
    )
    vacuum_method: Mapped[Optional["VacuumMethod"]] = relationship(
        lazy="selectin", foreign_keys=[vacuum_method_id]
    )
    cutting_method_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("cutting_method.id", ondelete="SET NULL")
    )
    cutting_method: Mapped[Optional["CuttingMethod"]] = relationship(
        lazy="selectin", foreign_keys=[cutting_method_id]
    )
    scraping_method_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("scraping_method.id", ondelete="SET NULL")
    )
    scraping_method: Mapped[Optional["ScrapingMethod"]] = relationship(
        lazy="selectin", foreign_keys=[scraping_method_id]
    )
    picking_method_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("picking_method.id", ondelete="SET NULL")
    )
    picking_method: Mapped[Optional["PickingMethod"]] = relationship(
        lazy="selectin", foreign_keys=[picking_method_id]
    )


from app.models.laboratory import Laboratory
from app.models.swab_method import SwabMethod
from app.models.tape_method import TapeMethod
from app.models.vacuum_method import VacuumMethod
from app.models.cutting_method import CuttingMethod
from app.models.scraping_method import ScrapingMethod
from app.models.picking_method import PickingMethod
