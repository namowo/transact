from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict, model_validator


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
    pass


class PCRContributorRead(PCRContributorBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    individual: Optional["IndividualRead"] = None


from app.schemas.individual import IndividualRead
