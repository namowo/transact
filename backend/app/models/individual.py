import uuid
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.sql import text

from app.core.db import Base


class Individual(Base):
    __tablename__ = "individual"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, index=True,
        server_default=text("gen_random_uuid()")
    )
    sex_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sex.id", ondelete="SET NULL")
    )
    sex: Mapped[Optional["Sex"]] = relationship(
        lazy="selectin", foreign_keys=[sex_id]
    )
    age: Mapped[Optional[int]]
    dna_shedding_propensity_category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dna_shedding_propensity_category.id", ondelete="SET NULL")
    )
    dna_shedding_propensity_category: Mapped[Optional["DNASheddingPropensityCategory"]] = (
        relationship(lazy="selectin", foreign_keys=[dna_shedding_propensity_category_id])
    )
    skin_disease_category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("skin_disease_category.id", ondelete="SET NULL")
    )
    skin_disease_category: Mapped[Optional["SkinDiseaseCategory"]] = relationship(
        lazy="selectin", foreign_keys=[skin_disease_category_id]
    )
    determination_of_shedding_propensity_category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("determination_of_shedding_propensity_category.id", ondelete="SET NULL")
    )
    determination_of_shedding_propensity_category: Mapped[Optional["DeterminationOfSheddingPropensityCategory"]] = relationship(
        lazy="selectin", foreign_keys=[determination_of_shedding_propensity_category_id]
    )


from app.models.skin_disease_category import SkinDiseaseCategory
from app.models.determination_of_shedding_propensity_category import DeterminationOfSheddingPropensityCategory
from app.models.sex import Sex
from app.models.dna_shedding_propensity_category import DNASheddingPropensityCategory
