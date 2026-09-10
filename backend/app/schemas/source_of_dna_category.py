from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class SourceOfDNACategoryBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class SourceOfDNACategoryCreate(SourceOfDNACategoryBase):
    pass


class SourceOfDNACategoryUpdate(SourceOfDNACategoryBase):
    pass


class SourceOfDNACategoryRead(SourceOfDNACategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
