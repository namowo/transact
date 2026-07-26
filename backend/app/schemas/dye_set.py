from typing import Optional

from pydantic import BaseModel, ConfigDict


class DyeSetBase(BaseModel):
    name: Optional[str] = None


class DyeSetCreate(DyeSetBase):
    pass


class DyeSetUpdate(DyeSetBase):
    pass


class DyeSetRead(DyeSetBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
