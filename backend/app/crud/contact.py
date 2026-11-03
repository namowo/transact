from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.contact import Contact
from app.schemas.contact import ContactCreate, ContactUpdate


class CRUDContact(CRUDBase[Contact, ContactCreate, ContactUpdate]):
    def __init__(self):
        super().__init__(Contact)

    async def _ensure_previous_unused(
        self, db: AsyncSession, previous_id: UUID | None, own_id: UUID | None = None
    ):
        """A contact can be followed by at most one other contact."""
        if previous_id is None:
            return
        stmt = select(Contact.id).where(Contact.previous_contact_id == previous_id)
        if own_id is not None:
            stmt = stmt.where(Contact.id != own_id)
        if (await db.execute(stmt)).first() is not None:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "This contact is already followed by another contact.",
            )

    async def create(self, db, obj_in, **kwargs):
        await self._ensure_previous_unused(db, obj_in.previous_contact_id)
        return await super().create(db, obj_in, **kwargs)

    async def update(self, db, id, obj_in, **kwargs):
        if "previous_contact_id" in obj_in.model_fields_set:
            await self._ensure_previous_unused(db, obj_in.previous_contact_id, id)
        # Explicit nulls must be stored so that chain links and names can be cleared.
        kwargs.setdefault("exclude_none", False)
        return await super().update(db, id, obj_in, **kwargs)


crud_contact = CRUDContact()
