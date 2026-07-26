from app.crud.base import CRUDBase
from app.models.statistical_software import StatisticalSoftware
from app.schemas.statistical_software import StatisticalSoftwareCreate, StatisticalSoftwareUpdate


class CRUDStatisticalSoftware(CRUDBase[StatisticalSoftware, StatisticalSoftwareCreate, StatisticalSoftwareUpdate]):
    def __init__(self):
        super().__init__(StatisticalSoftware)


crud_statistical_software = CRUDStatisticalSoftware()
