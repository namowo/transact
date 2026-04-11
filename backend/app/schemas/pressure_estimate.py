from typing import Optional

from pydantic import BaseModel, ConfigDict


class PressureEstimateBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PressureEstimateCreate(PressureEstimateBase):
    pass


class PressureEstimateUpdate(PressureEstimateBase):
    pass


class PressureEstimateRead(PressureEstimateBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
