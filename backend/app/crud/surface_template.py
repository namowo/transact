from app.crud.base import CRUDBase
from app.models.surface_template import SurfaceTemplate
from app.schemas.surface_template import SurfaceTemplateCreate, SurfaceTemplateUpdate


class CRUDSurfaceTemplate(
    CRUDBase[SurfaceTemplate, SurfaceTemplateCreate, SurfaceTemplateUpdate]
):
    def __init__(self):
        super().__init__(SurfaceTemplate)


crud_surface_template = CRUDSurfaceTemplate()
