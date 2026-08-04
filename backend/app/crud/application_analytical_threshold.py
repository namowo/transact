from app.crud.base import CRUDBase
from app.models.application_analytical_threshold import ApplicationAnalyticalThreshold
from app.schemas.application_analytical_threshold import (
    ApplicationAnalyticalThresholdCreate,
    ApplicationAnalyticalThresholdUpdate,
)


class CRUDApplicationAnalyticalThreshold(
    CRUDBase[
        ApplicationAnalyticalThreshold,
        ApplicationAnalyticalThresholdCreate,
        ApplicationAnalyticalThresholdUpdate,
    ]
):
    def __init__(self):
        super().__init__(ApplicationAnalyticalThreshold)


crud_application_analytical_threshold = CRUDApplicationAnalyticalThreshold()
