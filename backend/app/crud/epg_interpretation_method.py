from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.crud.exceptions import DatabaseCommitError
from app.models.epg_interpretation_method import EPGInterpretationMethod
from app.models.modelled_parameter import ModelledParameter
from app.models.user import User
from app.schemas.epg_interpretation_method import (
    EPGInterpretationMethodCreate,
    EPGInterpretationMethodUpdate,
)


class CRUDEPGInterpretationMethod(
    CRUDBase[EPGInterpretationMethod, EPGInterpretationMethodCreate, EPGInterpretationMethodUpdate]
):
    def __init__(self):
        super().__init__(EPGInterpretationMethod)

    async def _modelled_parameters_from(
        self, db: AsyncSession, ids: list[UUID]
    ) -> list[ModelledParameter]:
        if not ids:
            return []
        result = await db.execute(
            select(ModelledParameter).where(ModelledParameter.id.in_(ids))
        )
        return list(result.scalars().all())

    async def create(
        self, db: AsyncSession, obj_in: EPGInterpretationMethodCreate, user: Optional[User] = None
    ) -> EPGInterpretationMethod:
        obj_data = obj_in.model_dump(
            exclude_none=True, exclude_unset=True, exclude={"modelled_parameter_ids"}
        )
        new_instance = self.model(**obj_data)
        new_instance.modelled_parameters = await self._modelled_parameters_from(
            db, obj_in.modelled_parameter_ids
        )
        db.add(new_instance)

        try:
            await db.commit()
            await db.refresh(new_instance)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return new_instance

    async def update(
        self,
        db: AsyncSession,
        id,
        obj_in: EPGInterpretationMethodUpdate,
        exclude: dict = {},
        exclude_none: bool = True,
        exclude_unset: bool = True,
        user: Optional[User] = None,
    ) -> EPGInterpretationMethod:
        instance = await self.get(db, id)

        update_data = obj_in.model_dump(
            exclude={*exclude, "modelled_parameter_ids"},
            exclude_none=exclude_none,
            exclude_unset=exclude_unset,
        )
        for field, value in update_data.items():
            setattr(instance, field, value)

        if obj_in.modelled_parameter_ids is not None:
            instance.modelled_parameters = await self._modelled_parameters_from(
                db, obj_in.modelled_parameter_ids
            )

        try:
            await db.commit()
            await db.refresh(instance)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return instance


crud_epg_interpretation_method = CRUDEPGInterpretationMethod()
