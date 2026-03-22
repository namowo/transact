from typing import Optional

from pydantic import BaseModel, ConfigDict


class IndividualBase(BaseModel):
    sex: Optional[str] = None
    age: Optional[int] = None
    dna_shedding_propensity: Optional[str] = None
    skin_disease_category_id: Optional[int] = None
    determination_of_shedding_propensity_category_id: Optional[int] = None


class IndividualCreate(IndividualBase):
    pass


class IndividualUpdate(IndividualBase):
    pass


class IndividualRead(IndividualBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    skin_disease_category: Optional["SkinDiseaseCategoryRead"] = None
    determination_of_shedding_propensity_category: Optional["DeterminationOfSheddingPropensityCategoryRead"] = None


from app.schemas.skin_disease_category import SkinDiseaseCategoryRead
from app.schemas.determination_of_shedding_propensity_category import DeterminationOfSheddingPropensityCategoryRead
