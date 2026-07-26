from typing import Optional

from pydantic import BaseModel, ConfigDict


class QuantificationKitBase(BaseModel):
    name: Optional[str] = None


class QuantificationKitCreate(QuantificationKitBase):
    pass


class QuantificationKitUpdate(QuantificationKitBase):
    pass


class QuantificationKitRead(QuantificationKitBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
