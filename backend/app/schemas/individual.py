from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class IndividualBase(BaseModel):
    study_id: Optional[UUID] = None
    name: Optional[str] = None
    sex_id: Optional[UUID] = None
    age: Optional[int] = None
    dna_shedding_propensity_category_id: Optional[UUID] = None
    skin_disease_category_id: Optional[UUID] = None
    determination_of_shedding_propensity_category_id: Optional[UUID] = None


class IndividualCreate(IndividualBase):
    # Every individual must be used in at least one scenario.
    scenario_ids: list[UUID] = Field(min_length=1)


class IndividualUpdate(IndividualBase):
    # Omit to keep the current scenarios; when given, at least one is required.
    scenario_ids: Optional[list[UUID]] = Field(default=None, min_length=1)


class IndividualReadNested(IndividualBase):
    """Individual as embedded in Surface/PCRContributor reads - omits
    `scenario_ids`, whose relationship is too deep to lazy-load there."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sex: Optional["SexRead"] = None
    dna_shedding_propensity_category: Optional["DNASheddingPropensityCategoryRead"] = None
    skin_disease_category: Optional["SkinDiseaseCategoryRead"] = None
    determination_of_shedding_propensity_category: Optional["DeterminationOfSheddingPropensityCategoryRead"] = None


class IndividualRead(IndividualReadNested):
    scenario_ids: list[UUID] = []


from app.schemas.skin_disease_category import SkinDiseaseCategoryRead
from app.schemas.determination_of_shedding_propensity_category import DeterminationOfSheddingPropensityCategoryRead
from app.schemas.sex import SexRead
from app.schemas.dna_shedding_propensity_category import DNASheddingPropensityCategoryRead
