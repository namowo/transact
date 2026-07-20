from typing import Optional

from pydantic import BaseModel, ConfigDict


class SkinDiseaseCategoryBase(BaseModel):
    name: Optional[str] = None
    influence_on_shedding_propensity: Optional[bool] = None
    literature: Optional[str] = None


class SkinDiseaseCategoryCreate(SkinDiseaseCategoryBase):
    pass


class SkinDiseaseCategoryUpdate(SkinDiseaseCategoryBase):
    pass


class SkinDiseaseCategoryRead(SkinDiseaseCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
