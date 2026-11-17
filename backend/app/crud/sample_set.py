from app.crud.base import CRUDBase
from app.models.sample_set import SampleSet
from app.schemas.sample_set import SampleSetCreate, SampleSetUpdate


class CRUDSampleSet(CRUDBase[SampleSet, SampleSetCreate, SampleSetUpdate]):
    def __init__(self):
        super().__init__(SampleSet)


crud_sample_set = CRUDSampleSet()
