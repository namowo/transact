from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class SwabMethod(Base):
    __tablename__ = "swab_method"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    wetting_agent: Mapped[Optional[str]]
    volume_of_wetting_agent: Mapped[Optional[float]]
    specification: Mapped[Optional[str]]
    description: Mapped[Optional[str]]
    type_of_swab_category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("type_of_swab_category.id", ondelete="SET NULL")
    )
    type_of_swab_category: Mapped[Optional["TypeOfSwabCategory"]] = relationship(
        lazy="selectin", foreign_keys=[type_of_swab_category_id]
    )
    swabbing_technique_category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("swabbing_technique_category.id", ondelete="SET NULL")
    )
    swabbing_technique_category: Mapped[Optional["SwabbingTechniqueCategory"]] = (
        relationship(lazy="selectin", foreign_keys=[swabbing_technique_category_id])
    )


from app.models.type_of_swab_category import TypeOfSwabCategory
from app.models.swabbing_technique_category import SwabbingTechniqueCategory
