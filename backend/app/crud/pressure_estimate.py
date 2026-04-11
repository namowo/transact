from app.crud.base import CRUDBase
from app.models.pressure_estimate import PressureEstimate
from app.schemas.pressure_estimate import PressureEstimateCreate, PressureEstimateUpdate


class CRUDPressureEstimate(CRUDBase[PressureEstimate, PressureEstimateCreate, PressureEstimateUpdate]):
    def __init__(self):
        super().__init__(PressureEstimate)


crud_pressure_estimate = CRUDPressureEstimate()
