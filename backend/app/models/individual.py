from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Individual(Base):
    __tablename__ = "individual"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, unique=True, nullable=False
    )
    sex: Mapped[Optional[str]]
    age: Mapped[Optional[int]]
    dna_shedding_propensity: Mapped[Optional[str]]
    skin_disease_category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("skin_disease_category.id", ondelete="SET NULL")
    )
    skin_disease_category: Mapped[Optional["SkinDiseaseCategory"]] = relationship(
        lazy="selectin", foreign_keys=[skin_disease_category_id]
    )
    determination_of_shedding_propensity_category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("determination_of_shedding_propensity_category.id", ondelete="SET NULL")
    )
    determination_of_shedding_propensity_category: Mapped[Optional["DeterminationOfSheddingPropensityCategory"]] = relationship(
        lazy="selectin", foreign_keys=[determination_of_shedding_propensity_category_id]
    )


from app.models.skin_disease_category import SkinDiseaseCategory
from app.models.determination_of_shedding_propensity_category import DeterminationOfSheddingPropensityCategory
