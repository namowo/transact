from app.crud.base import CRUDBase
from app.models.stutter_filter import StutterFilter
from app.schemas.stutter_filter import StutterFilterCreate, StutterFilterUpdate


class CRUDStutterFilter(
    CRUDBase[StutterFilter, StutterFilterCreate, StutterFilterUpdate]
):
    def __init__(self):
        super().__init__(StutterFilter)


crud_stutter_filter = CRUDStutterFilter()
