from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ApiKeyCreate(BaseModel):
    name: Optional[str] = None
    expires_at: Optional[datetime] = None


class ApiKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: Optional[str] = None
    prefix: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class ApiKeyCreated(ApiKeyRead):
    token: str
