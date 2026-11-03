from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ThermoshakerBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ThermoshakerCreate(ThermoshakerBase):
    pass


class ThermoshakerUpdate(ThermoshakerBase):
    pass


class ThermoshakerRead(ThermoshakerBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
