from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Surface(Base):
    __tablename__ = "surface"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    individual_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("individual.id", ondelete="SET NULL")
    )
    individual: Mapped[Optional["Individual"]] = relationship(
        lazy="selectin", foreign_keys=[individual_id]
    )
    location_of_body_category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("location_of_body_category.id", ondelete="SET NULL")
    )
    location_of_body_category: Mapped[Optional["LocationOfBodyCategory"]] = relationship(
        lazy="selectin", foreign_keys=[location_of_body_category_id]
    )
    body_part_condition_category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("body_part_condition_category.id", ondelete="SET NULL")
    )
    body_part_condition_category: Mapped[Optional["BodyPartConditionCategory"]] = relationship(
        lazy="selectin", foreign_keys=[body_part_condition_category_id]
    )
    item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("item.id", ondelete="SET NULL")
    )
    item: Mapped[Optional["Item"]] = relationship(
        lazy="selectin", foreign_keys=[item_id]
    )
    item_parts_category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("item_parts_category.id", ondelete="SET NULL")
    )
    item_parts_category: Mapped[Optional["ItemPartsCategory"]] = relationship(
        lazy="selectin", foreign_keys=[item_parts_category_id]
    )
    condition_of_item_part_category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("condition_of_item_part_category.id", ondelete="SET NULL")
    )
    condition_of_item_part_category: Mapped[Optional["ConditionOfItemPartCategory"]] = relationship(
        lazy="selectin", foreign_keys=[condition_of_item_part_category_id]
    )
    surface_material_category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("surface_material_category.id", ondelete="SET NULL")
    )
    surface_material_category: Mapped[Optional["SurfaceMaterialCategory"]] = relationship(
        lazy="selectin", foreign_keys=[surface_material_category_id]
    )
    source_of_dna_category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("source_of_dna_category.id", ondelete="SET NULL")
    )
    source_of_dna_category: Mapped[Optional["SourceOfDNACategory"]] = relationship(
        lazy="selectin", foreign_keys=[source_of_dna_category_id]
    )
    photo: Mapped[Optional[str]]
    assumed_background_dna: Mapped[Optional[str]]
    assumed_prevalence: Mapped[Optional[bool]]
    further_description_of_assumed_background_and_prevalence: Mapped[Optional[str]]


from app.models.individual import Individual
from app.models.location_of_body_category import LocationOfBodyCategory
from app.models.body_part_condition_category import BodyPartConditionCategory
from app.models.item import Item
from app.models.item_parts_category import ItemPartsCategory
from app.models.condition_of_item_part_category import ConditionOfItemPartCategory
from app.models.surface_material_category import SurfaceMaterialCategory
from app.models.source_of_dna_category import SourceOfDNACategory
