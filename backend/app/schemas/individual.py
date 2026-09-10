from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class IndividualBase(BaseModel):
    sex_id: Optional[UUID] = None
    age: Optional[int] = None
    dna_shedding_propensity_category_id: Optional[UUID] = None
    skin_disease_category_id: Optional[UUID] = None
    determination_of_shedding_propensity_category_id: Optional[UUID] = None


class IndividualCreate(IndividualBase):
    pass


class IndividualUpdate(IndividualBase):
    pass


class IndividualRead(IndividualBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sex: Optional["SexRead"] = None
    dna_shedding_propensity_category: Optional["DNASheddingPropensityCategoryRead"] = None
    skin_disease_category: Optional["SkinDiseaseCategoryRead"] = None
    determination_of_shedding_propensity_category: Optional["DeterminationOfSheddingPropensityCategoryRead"] = None


from app.schemas.skin_disease_category import SkinDiseaseCategoryRead
from app.schemas.determination_of_shedding_propensity_category import DeterminationOfSheddingPropensityCategoryRead
from app.schemas.sex import SexRead
from app.schemas.dna_shedding_propensity_category import DNASheddingPropensityCategoryRead
