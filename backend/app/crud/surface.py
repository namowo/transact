from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.source_of_dna_category import SourceOfDNACategory
from app.models.surface import Surface
from app.schemas.surface import SurfaceCreate, SurfaceUpdate

ASSOCIATION_FIELDS = {
    "source_of_dna_category_ids": (SourceOfDNACategory, "source_of_dna_categories"),
}


class CRUDSurface(CRUDBase[Surface, SurfaceCreate, SurfaceUpdate]):
    def __init__(self):
        super().__init__(Surface)

    async def create(self, db: AsyncSession, obj_in: SurfaceCreate) -> Surface:
        return await self.create_with_associations(
            db, obj_in, association_fields=ASSOCIATION_FIELDS
        )

    async def update(
        self, db: AsyncSession, id: UUID, obj_in: SurfaceUpdate
    ) -> Surface:
        return await self.update_with_associations(
            db, id, obj_in, association_fields=ASSOCIATION_FIELDS
        )


crud_surface = CRUDSurface()
