from app.crud.base import CRUDBase
from app.models.sample import Sample
from app.schemas.sample import SampleCreate, SampleUpdate


class CRUDSample(CRUDBase[Sample, SampleCreate, SampleUpdate]):
    def __init__(self):
        super().__init__(Sample)


crud_sample = CRUDSample()
