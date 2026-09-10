from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class TypeOfTapeBase(BaseModel):
    name: str
    description: Optional[str] = None


class TypeOfTapeCreate(TypeOfTapeBase):
    pass


class TypeOfTapeUpdate(TypeOfTapeBase):
    pass


class TypeOfTapeRead(TypeOfTapeBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
