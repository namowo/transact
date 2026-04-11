from app.crud.base import CRUDBase
from app.models.friction_applied_estimate import FrictionAppliedEstimate
from app.schemas.friction_applied_estimate import FrictionAppliedEstimateCreate, FrictionAppliedEstimateUpdate


class CRUDFrictionAppliedEstimate(CRUDBase[FrictionAppliedEstimate, FrictionAppliedEstimateCreate, FrictionAppliedEstimateUpdate]):
    def __init__(self):
        super().__init__(FrictionAppliedEstimate)


crud_friction_applied_estimate = CRUDFrictionAppliedEstimate()
