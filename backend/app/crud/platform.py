from app.crud.base import CRUDBase
from app.models.platform import Platform
from app.schemas.platform import PlatformCreate, PlatformUpdate


class CRUDPlatform(CRUDBase[Platform, PlatformCreate, PlatformUpdate]):
    def __init__(self):
        super().__init__(Platform)


crud_platform = CRUDPlatform()
