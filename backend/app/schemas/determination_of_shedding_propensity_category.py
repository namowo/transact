from typing import Optional

from pydantic import BaseModel, ConfigDict


class DeterminationOfSheddingPropensityCategoryBase(BaseModel):
    authors: Optional[str] = None
    title: Optional[str] = None
    doi: Optional[str] = None
    restrictions_prior_to_sampling: Optional[str] = None
    monitored_transfer_factors: Optional[str] = None
    number_of_participants: Optional[str] = None
    replicates: Optional[str] = None
    shedder_test: Optional[str] = None
    classification_criteria: Optional[str] = None
    classification_scheme: Optional[str] = None
    classification_outcome: Optional[str] = None


class DeterminationOfSheddingPropensityCategoryCreate(DeterminationOfSheddingPropensityCategoryBase):
    pass


class DeterminationOfSheddingPropensityCategoryUpdate(DeterminationOfSheddingPropensityCategoryBase):
    pass


class DeterminationOfSheddingPropensityCategoryRead(DeterminationOfSheddingPropensityCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
