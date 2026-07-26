from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.contact_template import ContactTemplate
from app.models.scenario import Scenario
from app.schemas.contact_template import ContactTemplateCreate, ContactTemplateUpdate

ASSOCIATION_FIELDS = {"scenario_ids": (Scenario, "scenarios")}


class CRUDContactTemplate(
    CRUDBase[ContactTemplate, ContactTemplateCreate, ContactTemplateUpdate]
):
    def __init__(self):
        super().__init__(ContactTemplate)

    async def create(
        self, db: AsyncSession, obj_in: ContactTemplateCreate
    ) -> ContactTemplate:
        return await self.create_with_associations(
            db, obj_in, association_fields=ASSOCIATION_FIELDS
        )

    async def update(
        self, db: AsyncSession, id: int, obj_in: ContactTemplateUpdate
    ) -> ContactTemplate:
        return await self.update_with_associations(
            db, id, obj_in, association_fields=ASSOCIATION_FIELDS
        )


crud_contact_template = CRUDContactTemplate()
