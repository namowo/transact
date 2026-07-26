from typing import Optional

from pydantic import BaseModel, ConfigDict


class SexBase(BaseModel):
    name: Optional[str] = None


class SexCreate(SexBase):
    pass


class SexUpdate(SexBase):
    pass


class SexRead(SexBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
