from typing import Optional

from pydantic import BaseModel, ConfigDict


class WettingAgentBase(BaseModel):
    name: Optional[str] = None


class WettingAgentCreate(WettingAgentBase):
    pass


class WettingAgentUpdate(WettingAgentBase):
    pass


class WettingAgentRead(WettingAgentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
