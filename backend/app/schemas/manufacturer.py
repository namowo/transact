from typing import Optional

from pydantic import BaseModel, ConfigDict


class ManufacturerBase(BaseModel):
    name: Optional[str] = None


class ManufacturerCreate(ManufacturerBase):
    pass


class ManufacturerUpdate(ManufacturerBase):
    pass


class ManufacturerRead(ManufacturerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
