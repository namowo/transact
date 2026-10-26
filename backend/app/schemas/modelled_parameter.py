from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ModelledParameterBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ModelledParameterCreate(ModelledParameterBase):
    pass


class ModelledParameterUpdate(ModelledParameterBase):
    pass


class ModelledParameterRead(ModelledParameterBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
