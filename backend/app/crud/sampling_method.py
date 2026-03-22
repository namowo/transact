from app.crud.base import CRUDBase
from app.models.sampling_method import SamplingMethod
from app.schemas.sampling_method import SamplingMethodCreate, SamplingMethodUpdate


class CRUDSamplingMethod(CRUDBase[SamplingMethod, SamplingMethodCreate, SamplingMethodUpdate]):
    def __init__(self):
        super().__init__(SamplingMethod)


crud_sampling_method = CRUDSamplingMethod()
