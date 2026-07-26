from typing import Optional

from pydantic import BaseModel, ConfigDict


class SizeStandardBase(BaseModel):
    name: Optional[str] = None


class SizeStandardCreate(SizeStandardBase):
    pass


class SizeStandardUpdate(SizeStandardBase):
    pass


class SizeStandardRead(SizeStandardBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
