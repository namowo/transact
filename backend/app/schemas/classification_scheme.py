from typing import Optional

from pydantic import BaseModel, ConfigDict


class ClassificationSchemeBase(BaseModel):
    name: Optional[str] = None


class ClassificationSchemeCreate(ClassificationSchemeBase):
    pass


class ClassificationSchemeUpdate(ClassificationSchemeBase):
    pass


class ClassificationSchemeRead(ClassificationSchemeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
