from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PCRContributorBase(BaseModel):
    individual_id: Optional[UUID] = None
    unknown_label: Optional[str] = None
    mixture_proportion: Optional[float] = None

    @model_validator(mode="after")
    def _one_contributor_identity(self):
        if self.individual_id is not None and self.unknown_label is not None:
            raise ValueError("A contributor can't be both an individual and an unknown person.")
        return self


class PCRContributorCreate(PCRContributorBase):
    # Stored as a decimal fraction (0-1) with at most 5 decimal places.
    mixture_proportion: Optional[float] = Field(default=None, ge=0, le=1)

    @field_validator("mixture_proportion")
    @classmethod
    def _round_mixture_proportion(cls, value: Optional[float]) -> Optional[float]:
        return None if value is None else round(value, 5)


class PCRContributorRead(PCRContributorBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    individual: Optional["IndividualReadNested"] = None


from app.schemas.individual import IndividualReadNested
