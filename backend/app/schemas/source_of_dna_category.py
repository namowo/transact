from typing import Optional

from pydantic import BaseModel, ConfigDict


class SourceOfDNACategoryBase(BaseModel):
    source_of_dna_category: Optional[str] = None
    description: Optional[str] = None


class SourceOfDNACategoryCreate(SourceOfDNACategoryBase):
    pass


class SourceOfDNACategoryUpdate(SourceOfDNACategoryBase):
    pass


class SourceOfDNACategoryRead(SourceOfDNACategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
