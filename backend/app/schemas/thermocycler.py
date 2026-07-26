from typing import Optional

from pydantic import BaseModel, ConfigDict


class ThermocyclerBase(BaseModel):
    name: Optional[str] = None


class ThermocyclerCreate(ThermocyclerBase):
    pass


class ThermocyclerUpdate(ThermocyclerBase):
    pass


class ThermocyclerRead(ThermocyclerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
