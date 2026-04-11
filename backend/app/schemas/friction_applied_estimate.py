from typing import Optional

from pydantic import BaseModel, ConfigDict


class FrictionAppliedEstimateBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class FrictionAppliedEstimateCreate(FrictionAppliedEstimateBase):
    pass


class FrictionAppliedEstimateUpdate(FrictionAppliedEstimateBase):
    pass


class FrictionAppliedEstimateRead(FrictionAppliedEstimateBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
