from typing import Optional

from pydantic import BaseModel, ConfigDict


class StutterFilterBase(BaseModel):
    name: Optional[str] = None


class StutterFilterCreate(StutterFilterBase):
    pass


class StutterFilterUpdate(StutterFilterBase):
    pass


class StutterFilterRead(StutterFilterBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
