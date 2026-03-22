from typing import Optional

from pydantic import BaseModel, ConfigDict


class PrincipleOfExtractionMethodCategoryBase(BaseModel):
    principle_of_extraction_method_category: Optional[str] = None
    description: Optional[str] = None


class PrincipleOfExtractionMethodCategoryCreate(PrincipleOfExtractionMethodCategoryBase):
    pass


class PrincipleOfExtractionMethodCategoryUpdate(PrincipleOfExtractionMethodCategoryBase):
    pass


class PrincipleOfExtractionMethodCategoryRead(PrincipleOfExtractionMethodCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
