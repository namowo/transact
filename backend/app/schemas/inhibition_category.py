from typing import Optional

from pydantic import BaseModel, ConfigDict


class InhibitionCategoryBase(BaseModel):
    name: Optional[str] = None


class InhibitionCategoryCreate(InhibitionCategoryBase):
    pass


class InhibitionCategoryUpdate(InhibitionCategoryBase):
    pass


class InhibitionCategoryRead(InhibitionCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
