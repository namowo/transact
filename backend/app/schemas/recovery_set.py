from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class RecoverySetBase(BaseModel):
    name: Optional[str] = None


class RecoverySetCreate(RecoverySetBase):
    pass


class RecoverySetUpdate(RecoverySetBase):
    pass


class RecoverySetRead(RecoverySetBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
