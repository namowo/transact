from app.crud.base import CRUDBase
from app.models.surface import Surface
from app.schemas.surface import SurfaceCreate, SurfaceUpdate


class CRUDSurface(CRUDBase[Surface, SurfaceCreate, SurfaceUpdate]):
    def __init__(self):
        super().__init__(Surface)


crud_surface = CRUDSurface()
