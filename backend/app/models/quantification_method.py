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
    kit: Mapped[Optional[str]]
    manufacturer: Mapped[Optional[str]]
    platform: Mapped[Optional[str]]
    description_of_protocol: Mapped[Optional[str]]
    abbreviations_to_manufacturers_protocol: Mapped[Optional[str]]


from app.models.laboratory import Laboratory
from app.models.principle_of_quant_method_category import PrincipleOfQuantMethodCategory
