from typing import Optional

from pydantic import BaseModel, ConfigDict


class PolymerBase(BaseModel):
    name: Optional[str] = None


class PolymerCreate(PolymerBase):
    pass


class PolymerUpdate(PolymerBase):
    pass


class PolymerRead(PolymerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
