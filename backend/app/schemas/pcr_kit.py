from typing import Optional

from pydantic import BaseModel, ConfigDict


class PCRKitBase(BaseModel):
    name: Optional[str] = None


class PCRKitCreate(PCRKitBase):
    pass


class PCRKitUpdate(PCRKitBase):
    pass


class PCRKitRead(PCRKitBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
