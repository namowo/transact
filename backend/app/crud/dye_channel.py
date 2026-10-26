from app.crud.base import CRUDBase
from app.models.dye_channel import DyeChannel
from app.schemas.dye_channel import DyeChannelCreate, DyeChannelUpdate


class CRUDDyeChannel(CRUDBase[DyeChannel, DyeChannelCreate, DyeChannelUpdate]):
    def __init__(self):
        super().__init__(DyeChannel)


crud_dye_channel = CRUDDyeChannel()
