from typing import Optional

from pydantic import BaseModel, ConfigDict


class PrincipleOfExtractionMethodCategoryBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PrincipleOfExtractionMethodCategoryCreate(PrincipleOfExtractionMethodCategoryBase):
    pass


class PrincipleOfExtractionMethodCategoryUpdate(PrincipleOfExtractionMethodCategoryBase):
    pass


class PrincipleOfExtractionMethodCategoryRead(PrincipleOfExtractionMethodCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
