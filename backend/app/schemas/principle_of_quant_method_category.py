from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class PrincipleOfQuantMethodCategoryBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PrincipleOfQuantMethodCategoryCreate(PrincipleOfQuantMethodCategoryBase):
    pass


class PrincipleOfQuantMethodCategoryUpdate(PrincipleOfQuantMethodCategoryBase):
    pass


class PrincipleOfQuantMethodCategoryRead(PrincipleOfQuantMethodCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
