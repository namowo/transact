from typing import Optional

from pydantic import BaseModel, ConfigDict


class DNASheddingPropensityCategoryBase(BaseModel):
    name: Optional[str] = None


class DNASheddingPropensityCategoryCreate(DNASheddingPropensityCategoryBase):
    pass


class DNASheddingPropensityCategoryUpdate(DNASheddingPropensityCategoryBase):
    pass


class DNASheddingPropensityCategoryRead(DNASheddingPropensityCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
