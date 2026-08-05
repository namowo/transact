from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.common import SecondsTimedelta


class DeterminationOfSheddingPropensityCategoryRestrictionBase(BaseModel):
    restriction_prior_to_sampling_id: int
    duration: Optional[SecondsTimedelta] = None


class DeterminationOfSheddingPropensityCategoryRestrictionCreate(
    DeterminationOfSheddingPropensityCategoryRestrictionBase
):
    pass


class DeterminationOfSheddingPropensityCategoryRestrictionRead(
    DeterminationOfSheddingPropensityCategoryRestrictionBase
):
    model_config = ConfigDict(from_attributes=True)

    restriction_prior_to_sampling: Optional["RestrictionPriorToSamplingRead"] = None


from app.schemas.restriction_prior_to_sampling import RestrictionPriorToSamplingRead
