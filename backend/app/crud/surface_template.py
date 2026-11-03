from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.source_of_dna_category import SourceOfDNACategory
from app.models.surface_template import SurfaceTemplate
from app.schemas.surface_template import SurfaceTemplateCreate, SurfaceTemplateUpdate

ASSOCIATION_FIELDS = {
    "source_of_dna_category_ids": (SourceOfDNACategory, "source_of_dna_categories"),
}


class CRUDSurfaceTemplate(
    CRUDBase[SurfaceTemplate, SurfaceTemplateCreate, SurfaceTemplateUpdate]
):
    def __init__(self):
        super().__init__(SurfaceTemplate)

    async def create(
        self, db: AsyncSession, obj_in: SurfaceTemplateCreate
    ) -> SurfaceTemplate:
        return await self.create_with_associations(
            db, obj_in, association_fields=ASSOCIATION_FIELDS
        )

    async def update(
        self, db: AsyncSession, id: UUID, obj_in: SurfaceTemplateUpdate
    ) -> SurfaceTemplate:
        return await self.update_with_associations(
            db, id, obj_in, association_fields=ASSOCIATION_FIELDS
        )


crud_surface_template = CRUDSurfaceTemplate()
