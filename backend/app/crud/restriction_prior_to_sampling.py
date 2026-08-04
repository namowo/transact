from app.crud.base import CRUDBase
from app.models.restriction_prior_to_sampling import RestrictionPriorToSampling
from app.schemas.restriction_prior_to_sampling import (
    RestrictionPriorToSamplingCreate,
    RestrictionPriorToSamplingUpdate,
)


class CRUDRestrictionPriorToSampling(
    CRUDBase[
        RestrictionPriorToSampling,
        RestrictionPriorToSamplingCreate,
        RestrictionPriorToSamplingUpdate,
    ]
):
    def __init__(self):
        super().__init__(RestrictionPriorToSampling)


crud_restriction_prior_to_sampling = CRUDRestrictionPriorToSampling()
