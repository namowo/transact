from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Surface(Base):
    """An actual, realized instance of a SurfaceTemplate used within a Contact."""

    __tablename__ = "surface"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    surface_template_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("surface_template.id", ondelete="SET NULL")
    )
    surface_template: Mapped[Optional["SurfaceTemplate"]] = relationship(
        lazy="selectin", foreign_keys=[surface_template_id]
    )
    individual_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("individual.id", ondelete="SET NULL")
    )
    individual: Mapped[Optional["Individual"]] = relationship(
        lazy="selectin", foreign_keys=[individual_id]
    )
    # The following override the corresponding SurfaceTemplate attribute when set;
    # a null value means the template's value applies.
    location_of_body_category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("location_of_body_category.id", ondelete="SET NULL")
    )
    location_of_body_category: Mapped[Optional["LocationOfBodyCategory"]] = (
        relationship(lazy="selectin", foreign_keys=[location_of_body_category_id])
    )
    body_part_condition_category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("body_part_condition_category.id", ondelete="SET NULL")
    )
    body_part_condition_category: Mapped[Optional["BodyPartConditionCategory"]] = (
        relationship(lazy="selectin", foreign_keys=[body_part_condition_category_id])
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
    condition_of_item_part_category: Mapped[Optional["ConditionOfItemPartCategory"]] = (
        relationship(lazy="selectin", foreign_keys=[condition_of_item_part_category_id])
    )
    surface_material_category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("surface_material_category.id", ondelete="SET NULL")
    )
    surface_material_category: Mapped[Optional["SurfaceMaterialCategory"]] = (
        relationship(lazy="selectin", foreign_keys=[surface_material_category_id])
    )
    source_of_dna_category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("source_of_dna_category.id", ondelete="SET NULL")
    )
    source_of_dna_category: Mapped[Optional["SourceOfDNACategory"]] = relationship(
        lazy="selectin", foreign_keys=[source_of_dna_category_id]
    )


from app.models.surface_template import SurfaceTemplate
from app.models.individual import Individual
from app.models.location_of_body_category import LocationOfBodyCategory
from app.models.body_part_condition_category import BodyPartConditionCategory
from app.models.item_parts_category import ItemPartsCategory
from app.models.condition_of_item_part_category import ConditionOfItemPartCategory
from app.models.surface_material_category import SurfaceMaterialCategory
from app.models.source_of_dna_category import SourceOfDNACategory
