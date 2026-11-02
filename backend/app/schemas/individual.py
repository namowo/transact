from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class IndividualBase(BaseModel):
    study_id: Optional[UUID] = None
    name: Optional[str] = None
    sex_id: Optional[UUID] = None
    age: Optional[int] = None
    dna_shedding_propensity_category_id: Optional[UUID] = None
    skin_disease_category_id: Optional[UUID] = None
    determination_of_shedding_propensity_category_id: Optional[UUID] = None


class IndividualCreate(IndividualBase):
    scenario_ids: list[UUID] = []


class IndividualUpdate(IndividualBase):
    scenario_ids: Optional[list[UUID]] = None


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
