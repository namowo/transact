from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.contact import Contact
from app.models.surface import Surface
from app.models.surface_template import SurfaceTemplate
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

    async def _ensure_surfaces_unshared(
        self,
        db: AsyncSession,
        donor_id: UUID | None,
        recipient_id: UUID | None,
        own_id: UUID | None = None,
        changed: set[str] | None = None,
    ):
        """Each actual contact uses its own item surfaces: contacts with the
        same tool use the same kind of item, never the identical surface
        ("das gleiche, aber nicht dasselbe"). A contact also cannot use one
        surface as both donor and recipient.

        `changed` limits the sharing check to the given sides, so editing one
        side of an older contact is not blocked by the other, untouched side."""
        if donor_id is not None and donor_id == recipient_id:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "A surface cannot be both donor and recipient of the same contact.",
            )
        sides = {"donor_surface_id": donor_id, "recipient_surface_id": recipient_id}
        surface_ids = [
            sid
            for side, sid in sides.items()
            if sid is not None and (changed is None or side in changed)
        ]
        if not surface_ids:
            return
        stmt = (
            select(Contact.id)
            .join(
                Surface,
                or_(
                    Surface.id == Contact.donor_surface_id,
                    Surface.id == Contact.recipient_surface_id,
                ),
            )
            .join(SurfaceTemplate, SurfaceTemplate.id == Surface.surface_template_id)
            .where(Surface.id.in_(surface_ids), SurfaceTemplate.item_id.is_not(None))
        )
        if own_id is not None:
            stmt = stmt.where(Contact.id != own_id)
        if (await db.execute(stmt)).first() is not None:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "This item surface is already used by another contact. "
                "Each contact needs its own surface of the item.",
            )

    async def create(self, db, obj_in, **kwargs):
        await self._ensure_previous_unused(db, obj_in.previous_contact_id)
        await self._ensure_surfaces_unshared(
            db, obj_in.donor_surface_id, obj_in.recipient_surface_id
        )
        return await super().create(db, obj_in, **kwargs)

    async def update(self, db, id, obj_in, **kwargs):
        if "previous_contact_id" in obj_in.model_fields_set:
            await self._ensure_previous_unused(db, obj_in.previous_contact_id, id)
        surface_fields = {"donor_surface_id", "recipient_surface_id"}
        if surface_fields & obj_in.model_fields_set:
            current = await db.get(Contact, id)
            donor_id = (
                obj_in.donor_surface_id
                if "donor_surface_id" in obj_in.model_fields_set
                else getattr(current, "donor_surface_id", None)
            )
            recipient_id = (
                obj_in.recipient_surface_id
                if "recipient_surface_id" in obj_in.model_fields_set
                else getattr(current, "recipient_surface_id", None)
            )
            await self._ensure_surfaces_unshared(
                db,
                donor_id,
                recipient_id,
                id,
                changed=surface_fields & obj_in.model_fields_set,
            )
        # Explicit nulls must be stored so that chain links and names can be cleared.
        kwargs.setdefault("exclude_none", False)
        return await super().update(db, id, obj_in, **kwargs)


crud_contact = CRUDContact()
