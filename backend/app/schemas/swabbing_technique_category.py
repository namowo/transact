from typing import Optional

from pydantic import BaseModel, ConfigDict


class SwabbingTechniqueCategoryBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class SwabbingTechniqueCategoryCreate(SwabbingTechniqueCategoryBase):
    pass


class SwabbingTechniqueCategoryUpdate(SwabbingTechniqueCategoryBase):
    pass


class SwabbingTechniqueCategoryRead(SwabbingTechniqueCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
