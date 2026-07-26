from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class QuantificationMethod(Base):
    __tablename__ = "quantification_method"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    laboratory_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("laboratory.id", ondelete="SET NULL")
    )
    laboratory: Mapped[Optional["Laboratory"]] = relationship(
        lazy="selectin", foreign_keys=[laboratory_id]
    )
    principle_of_quant_method_category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("principle_of_quant_method_category.id", ondelete="SET NULL")
    )
    principle_of_quant_method_category: Mapped[
        Optional["PrincipleOfQuantMethodCategory"]
    ] = relationship(
        lazy="selectin", foreign_keys=[principle_of_quant_method_category_id]
    )
    kit_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("quantification_kit.id", ondelete="SET NULL")
    )
    kit: Mapped[Optional["QuantificationKit"]] = relationship(
        lazy="selectin", foreign_keys=[kit_id]
    )
    manufacturer_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("manufacturer.id", ondelete="SET NULL")
    )
    manufacturer: Mapped[Optional["Manufacturer"]] = relationship(
        lazy="selectin", foreign_keys=[manufacturer_id]
    )
    platform_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("platform.id", ondelete="SET NULL")
    )
    platform: Mapped[Optional["Platform"]] = relationship(
        lazy="selectin", foreign_keys=[platform_id]
    )
    description_of_protocol: Mapped[Optional[str]]
    abbreviations_to_manufacturers_protocol: Mapped[Optional[str]]


from app.models.laboratory import Laboratory
from app.models.principle_of_quant_method_category import PrincipleOfQuantMethodCategory
from app.models.quantification_kit import QuantificationKit
from app.models.manufacturer import Manufacturer
from app.models.platform import Platform
