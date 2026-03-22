from app.crud.base import CRUDBase
from app.models.picking_method import PickingMethod
from app.schemas.picking_method import PickingMethodCreate, PickingMethodUpdate


class CRUDPickingMethod(CRUDBase[PickingMethod, PickingMethodCreate, PickingMethodUpdate]):
    def __init__(self):
        super().__init__(PickingMethod)


crud_picking_method = CRUDPickingMethod()
