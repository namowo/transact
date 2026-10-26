import uuid
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.sql import text

from app.core.db import Base


class QuantificationMethod(Base):
    __tablename__ = "quantification_method"

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
    principle_of_quant_method_category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("principle_of_quant_method_category.id", ondelete="SET NULL")
    )
    principle_of_quant_method_category: Mapped[
        Optional["PrincipleOfQuantMethodCategory"]
    ] = relationship(
        lazy="selectin", foreign_keys=[principle_of_quant_method_category_id]
    )
    kit_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("quantification_kit.id", ondelete="SET NULL")
    )
    kit: Mapped[Optional["QuantificationKit"]] = relationship(
        lazy="selectin", foreign_keys=[kit_id]
    )
    platform_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("quantification_platform.id", ondelete="SET NULL")
    )
    platform: Mapped[Optional["QuantificationPlatform"]] = relationship(
        lazy="selectin", foreign_keys=[platform_id]
    )
    abbreviations_to_manufacturers_protocol: Mapped[Optional[str]]


from app.models.laboratory import Laboratory
from app.models.principle_of_quant_method_category import PrincipleOfQuantMethodCategory
from app.models.quantification_kit import QuantificationKit
from app.models.quantification_platform import QuantificationPlatform
