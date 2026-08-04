from typing import Optional

from pydantic import BaseModel, ConfigDict


class MonitoredTransferFactorBase(BaseModel):
    name: Optional[str] = None


class MonitoredTransferFactorCreate(MonitoredTransferFactorBase):
    pass


class MonitoredTransferFactorUpdate(MonitoredTransferFactorBase):
    pass


class MonitoredTransferFactorRead(MonitoredTransferFactorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
