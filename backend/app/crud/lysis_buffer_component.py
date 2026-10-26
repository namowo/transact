from app.crud.base import CRUDBase
from app.models.lysis_buffer_component import LysisBufferComponent
from app.schemas.lysis_buffer_component import LysisBufferComponentCreate, LysisBufferComponentUpdate


class CRUDLysisBufferComponent(CRUDBase[LysisBufferComponent, LysisBufferComponentCreate, LysisBufferComponentUpdate]):
    def __init__(self):
        super().__init__(LysisBufferComponent)


crud_lysis_buffer_component = CRUDLysisBufferComponent()
